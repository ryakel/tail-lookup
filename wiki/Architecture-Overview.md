# Architecture Overview

This document provides a comprehensive overview of the tail-lookup system architecture, design decisions, and component interactions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Clients                              │
│  (Web Browser, API Consumers, Mobile Apps, Scripts)         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   API Endpoints                       │  │
│  │  • GET  /api/v1/aircraft/{tail}                      │  │
│  │  • POST /api/v1/aircraft/bulk                        │  │
│  │  • GET  /api/v1/health                               │  │
│  │  • GET  /api/v1/stats                                │  │
│  │  • GET  / (Web UI)                                   │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │              Pydantic Models                          │  │
│  │  (Request/Response Validation & Serialization)       │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │             Database Layer (database.py)             │  │
│  │  • N-number normalization                            │  │
│  │  • Aircraft/Engine type mappings                     │  │
│  │  • JOIN optimization                                 │  │
│  └────────────────────┬─────────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  master table      (~300K records)                   │  │
│  │  • n_number, mfr_mdl_code, year_mfr, etc.           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  acftref table     (Aircraft model reference)        │  │
│  │  • code, mfr, model, type_acft, type_eng, etc.      │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  metadata table    (Update tracking)                 │  │
│  │  • key, value (last_updated timestamp)              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Single Lookup Flow

1. **Client Request**: `GET /api/v1/aircraft/N172SP`
2. **FastAPI Routing**: Route handler in `main.py` receives request
3. **N-number Normalization**: Convert "N172SP" → "172SP" (strip N prefix, uppercase)
4. **Database Query**: Execute JOIN query between `master` and `acftref` tables
5. **Type Mapping**: Convert numeric codes to human-readable strings (e.g., "4" → "Fixed Wing Single-Engine")
6. **Response Validation**: Pydantic model validates and serializes response
7. **Client Response**: JSON with aircraft details or 404 if not found

### Bulk Lookup Flow

1. **Client Request**: `POST /api/v1/aircraft/bulk` with JSON array of tail numbers
2. **Request Validation**: Pydantic validates max 50 tail numbers
3. **Batch Processing**: Iterate through each tail number
4. **Individual Lookups**: Same lookup flow as single, but collect all results
5. **Error Handling**: Failed lookups return with error message, don't fail entire request
6. **Response Aggregation**: Return total count, found count, and results array
7. **Client Response**: JSON with bulk results

### Database Update Flow

1. **Scheduled Trigger**: GitHub Actions cron at 6 AM UTC daily
2. **Download FAA Data**: Fetch ReleasableAircraft.zip (~30MB)
3. **Parse MASTER.txt**: Extract ~300K aircraft registrations
4. **Parse ACFTREF.txt**: Extract aircraft model reference data
5. **Build SQLite Database**: Create tables, insert data, create indexes
6. **Docker Build**: Bake database into Docker image
7. **Publish**: Push to Docker Hub with `latest` and date tags
8. **Release**: Create GitHub Release with database file attachment
9. **Optional Webhook**: Trigger Portainer for auto-deployment

## Component Details

### FastAPI Application (`app/main.py`)

**Purpose**: Main application entry point, route definitions, middleware configuration

**Key Features**:
- CORS middleware for cross-origin requests
- Lifespan context manager for database connection handling
- N-number normalization function
- OpenAPI/Swagger automatic documentation
- Static file serving for web UI

**Design Decisions**:
- **Why FastAPI?** Modern async framework, automatic OpenAPI docs, excellent performance, Pydantic integration
- **Why CORS enabled?** Allow web apps from different origins to use the API
- **Why lifespan context?** Clean database connection management, proper startup/shutdown

### Database Layer (`app/database.py`)

**Purpose**: SQLite operations, type mappings, data access abstraction

**Key Features**:
- Singleton database connection pattern
- Aircraft type code to name mapping (11 types)
- Engine type code to name mapping (12 types)
- JOIN optimization between master and acftref tables
- Optional field handling (None for missing data)

**Design Decisions**:
- **Why SQLite?** Lightweight (~25MB), zero configuration, baked into Docker image, sufficient for read-heavy workload
- **Why JOIN query?** Single query is more efficient than multiple lookups
- **Why code mappings in Python?** FAA database has numeric codes, we provide human-readable names

**Database Schema**:
```sql
-- master table
CREATE TABLE master (
    n_number TEXT PRIMARY KEY,
    serial_number TEXT,
    mfr_mdl_code TEXT,
    year_mfr INTEGER,
    -- ... other fields
);

-- acftref table
CREATE TABLE acftref (
    code TEXT PRIMARY KEY,
    mfr TEXT,
    model TEXT,
    type_acft TEXT,
    type_eng TEXT,
    no_eng INTEGER,
    no_seats INTEGER,
    -- ... other fields
);

-- metadata table
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Index for JOIN optimization
CREATE INDEX idx_mfr_mdl_code ON master(mfr_mdl_code);
```

### Pydantic Models (`app/models.py`)

**Purpose**: Type-safe request/response models, validation, serialization

**Models**:
- `AircraftResponse`: Single aircraft lookup response
- `BulkRequest`: Bulk lookup request (max 50 tail numbers)
- `BulkResult`: Single result within bulk response
- `BulkResponse`: Bulk lookup response with counts and results
- `HealthResponse`: Health check response
- `StatsResponse`: Database statistics response

**Design Decisions**:
- **Why Pydantic?** Automatic validation, serialization, OpenAPI schema generation
- **Why Optional fields?** Not all aircraft have all data (e.g., year_mfr may be unknown)
- **Why max 50 for bulk?** Balance between usability and server load

### Data Pipeline (`scripts/update_faa_data.py`)

**Purpose**: Download FAA data, parse files, build SQLite database

**Process**:
1. Download ReleasableAircraft.zip from FAA website
2. Extract MASTER.txt (fixed-width format)
3. Extract ACFTREF.txt (fixed-width format)
4. Parse both files using column positions
5. Create SQLite database with three tables
6. Insert all records in batch for performance
7. Create index on mfr_mdl_code for JOIN optimization
8. Store last_updated timestamp in metadata table

**Design Decisions**:
- **Why fixed-width parsing?** FAA format is fixed-width, not CSV
- **Why batch insert?** Much faster than individual inserts (~300K records)
- **Why index on mfr_mdl_code?** This is the JOIN key, indexing improves query performance
- **Why store metadata?** Track when data was last updated for health checks

**FAA Data Format**:
- MASTER.txt: Fixed-width columns, ~300K rows, aircraft registration data
- ACFTREF.txt: Fixed-width columns, aircraft model reference
- Updated daily by FAA at 11:30 PM CT (5:30 AM UTC)
- Download URL: https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download

### Web UI (`app/static/index.html`)

**Purpose**: Browser-based interface for testing the API

**Features**:
- Dark theme (Tailwind-inspired colors)
- Tab-based interface (Single/Bulk lookup)
- Real-time validation
- Error handling with user-friendly messages
- Responsive design for mobile
- Database statistics display

**Design Decisions**:
- **Why single-file HTML?** Simple, no build process, easy to maintain
- **Why dark theme?** Modern aesthetic, easier on eyes
- **Why tabs?** Clear separation of single vs bulk lookup

## Deployment Architecture

### Docker Container

**Base Image**: `python:3.12-slim`
**Port**: 8080
**Health Check**: HTTP GET to `/api/v1/health` every 30s

**Container Contents**:
- Python application code (`/app/app/`)
- SQLite database (`/app/data/aircraft.db`)
- Python dependencies (FastAPI, Uvicorn, Pydantic)

**Design Decisions**:
- **Why baked-in database?** Zero-configuration deployment, no external database needed
- **Why slim image?** Smaller image size (~150MB vs ~1GB for full Python image)
- **Why port 8080?** Standard non-privileged port, easily mappable

### CI/CD Pipeline

See [CI/CD Pipeline](CI-CD-Pipeline) for detailed workflow documentation.

**Primary Workflows**:
1. **Nightly Build** (`nightly-build.yml`): Daily at 6 AM UTC
2. **Main Branch Build** (`build-main.yml`): On push to main, handles versioning and releases
3. **Develop Branch Build** (`build-develop.yml`): On push to develop branch

**Design Decisions**:
- **Why 6 AM UTC?** FAA updates at 11:30 PM CT (5:30 AM UTC), 30min buffer
- **Why two workflows?** Separate concerns: data updates vs code changes
- **Why Docker Hub?** Popular, reliable, free for public images
- **Why GitHub Releases?** Provide database snapshots for manual download

## Performance Considerations

### Database Performance

- **SQLite read performance**: Excellent for read-heavy workloads (~1000s queries/sec)
- **JOIN optimization**: Index on mfr_mdl_code improves JOIN performance
- **File-based**: No network latency, database is local to application
- **Size**: ~25MB database, easily fits in memory for OS-level caching

### API Performance

- **Async FastAPI**: Non-blocking I/O, handles concurrent requests efficiently
- **Pydantic validation**: Fast native validation, minimal overhead
- **Static typing**: Python 3.12 type hints improve performance
- **Uvicorn**: High-performance ASGI server

### Scalability

**Current Design**:
- Single container handles ~1000s requests/sec (read-only workload)
- Database fits in memory on most systems
- No external dependencies or network calls

**Scaling Options**:
1. **Horizontal scaling**: Run multiple containers behind load balancer
2. **CDN caching**: Cache responses for common tail numbers
3. **Read replicas**: Distribute database file to multiple containers
4. **PostgreSQL migration**: If write workload increases or multi-container writes needed

## Security Considerations

### API Security

- **No authentication required**: Public FAA data, open access by design
- **CORS enabled**: Allow cross-origin requests
- **Input validation**: Pydantic validates all inputs
- **SQL injection**: Using parameterized queries, safe from injection

### Container Security

- **Non-root user**: Container runs as non-root (TODO: verify in Dockerfile)
- **Minimal base image**: python:3.12-slim reduces attack surface
- **No secrets in image**: No credentials or API keys
- **Read-only database**: Database is read-only, no write operations

### CI/CD Security

- **GitHub Actions permissions**: Minimal permissions (contents:write, packages:write)
- **Secrets management**: Docker Hub credentials stored as GitHub Secrets
- **Renovate**: Automated dependency updates with intelligent scheduling and auto-merge capabilities

## Future Considerations

### Potential Enhancements

1. **Caching layer**: Redis for frequently requested tail numbers
2. **Rate limiting**: Prevent abuse of bulk endpoint
3. **API authentication**: Optional API keys for tracking/quotas
4. **WebSocket updates**: Real-time notifications of database updates
5. **Search functionality**: Search by manufacturer, model, year
6. **Historical data**: Track changes over time
7. **Multi-region deployment**: Deploy to multiple regions for lower latency
8. **Monitoring**: Prometheus metrics, Grafana dashboards
9. **PostgreSQL option**: Alternative backend for high-concurrency workloads

### Known Limitations

1. **Single database file**: No real-time updates, requires container restart
2. **No write API**: Read-only by design
3. **US registrations only**: FAA data only covers US-registered aircraft
4. **No historical data**: Only current registrations, no change tracking
5. **Bulk limit**: Max 50 tail numbers per request

## References

- [FAA Releasable Aircraft Database](https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
