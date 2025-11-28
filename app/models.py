"""Pydantic models for tail-lookup API responses."""
from typing import Optional, List
from pydantic import BaseModel, Field


class AircraftResponse(BaseModel):
    """Aircraft registration lookup response."""
    tail_number: str
    manufacturer: str
    model: str
    series: Optional[str] = None
    aircraft_type: str
    engine_type: str
    num_engines: Optional[int] = None
    num_seats: Optional[int] = None
    year_mfr: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "tail_number": "N172SP",
                "manufacturer": "CESSNA",
                "model": "172S",
                "series": "SKYHAWK SP",
                "aircraft_type": "Fixed Wing Single-Engine",
                "engine_type": "Reciprocating",
                "num_engines": 1,
                "num_seats": 4,
                "year_mfr": 2001
            }
        }
    }


class BulkRequest(BaseModel):
    """Bulk lookup request."""
    tail_numbers: List[str] = Field(..., max_length=50)

    model_config = {
        "json_schema_extra": {
            "example": {
                "tail_numbers": ["N172SP", "N12345", "N67890"]
            }
        }
    }


class BulkResult(BaseModel):
    """Single result within bulk response."""
    tail_number: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    series: Optional[str] = None
    aircraft_type: Optional[str] = None
    engine_type: Optional[str] = None
    num_engines: Optional[int] = None
    num_seats: Optional[int] = None
    year_mfr: Optional[int] = None
    error: Optional[str] = None


class BulkResponse(BaseModel):
    """Bulk lookup response."""
    total: int
    found: int
    results: List[BulkResult]

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 3,
                "found": 2,
                "results": [
                    {
                        "tail_number": "N172SP",
                        "manufacturer": "CESSNA",
                        "model": "172S",
                        "aircraft_type": "Fixed Wing Single-Engine",
                        "engine_type": "Reciprocating"
                    },
                    {
                        "tail_number": "N99999",
                        "error": "Not found"
                    }
                ]
            }
        }
    }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database_exists: bool
    record_count: int
    last_updated: Optional[str] = None


class StatsResponse(BaseModel):
    """Database statistics response."""
    record_count: int
    last_updated: Optional[str] = None
