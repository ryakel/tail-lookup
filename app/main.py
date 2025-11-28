"""tail-lookup: FAA Aircraft Registration Lookup API"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List

from database import Database
from models import AircraftResponse, HealthResponse, StatsResponse, BulkRequest, BulkResponse, BulkResult

DB_PATH = os.getenv("DB_PATH", "/app/data/aircraft.db")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

db: Database = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    if not os.path.exists(DB_PATH):
        raise RuntimeError(f"Database not found at {DB_PATH}")
    db = Database(DB_PATH)
    yield
    db.close()


app = FastAPI(
    title="tail-lookup",
    description="FAA Aircraft Registration Lookup API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def normalize_tail(tail: str) -> str:
    """Normalize N-number: uppercase, strip N prefix and dashes."""
    t = tail.upper().strip()
    if t.startswith("N"):
        t = t[1:]
    return t.replace("-", "").replace(" ", "")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the UI."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/v1/aircraft/{tail}", response_model=AircraftResponse)
async def get_aircraft(tail: str):
    """Lookup aircraft by N-number (e.g., N172SP, 172SP, N-172SP)."""
    normalized = normalize_tail(tail)
    if not normalized:
        raise HTTPException(400, "Invalid tail number")

    aircraft = db.lookup(normalized)
    if not aircraft:
        raise HTTPException(404, f"Aircraft N{normalized} not found")

    return aircraft


@app.post("/api/v1/aircraft/bulk", response_model=BulkResponse)
async def bulk_lookup(request: BulkRequest):
    """Lookup multiple aircraft by N-number. Maximum 50 per request."""
    if len(request.tail_numbers) > 50:
        raise HTTPException(400, "Maximum 50 tail numbers per request")

    results: List[BulkResult] = []
    found = 0

    for tail in request.tail_numbers:
        normalized = normalize_tail(tail)
        if not normalized:
            results.append(BulkResult(
                tail_number=tail.upper(),
                error="Invalid tail number"
            ))
            continue

        aircraft = db.lookup(normalized)
        if aircraft:
            found += 1
            results.append(BulkResult(
                tail_number=aircraft.tail_number,
                manufacturer=aircraft.manufacturer,
                model=aircraft.model,
                series=aircraft.series,
                aircraft_type=aircraft.aircraft_type,
                engine_type=aircraft.engine_type,
                num_engines=aircraft.num_engines,
                num_seats=aircraft.num_seats,
                year_mfr=aircraft.year_mfr
            ))
        else:
            results.append(BulkResult(
                tail_number=f"N{normalized}",
                error="Not found"
            ))

    return BulkResponse(
        total=len(request.tail_numbers),
        found=found,
        results=results
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    """Health check with database status."""
    stats = db.get_stats()
    return HealthResponse(
        status="healthy" if stats.record_count > 0 else "degraded",
        database_exists=os.path.exists(DB_PATH),
        record_count=stats.record_count,
        last_updated=stats.last_updated
    )


@app.get("/api/v1/stats", response_model=StatsResponse)
async def stats():
    """Database statistics."""
    return db.get_stats()
