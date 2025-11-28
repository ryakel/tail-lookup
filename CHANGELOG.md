# Changelog

All notable changes to tail-lookup will be documented in this file.

## [Unreleased]

### Added
- Initial project structure and repository setup
- Core FastAPI application with 5 endpoints:
  - `GET /api/v1/aircraft/{tail}` - Single aircraft lookup
  - `POST /api/v1/aircraft/bulk` - Bulk lookup (up to 50 aircraft)
  - `GET /api/v1/health` - Health check with database status
  - `GET /api/v1/stats` - Database statistics
  - `GET /` - Web UI
- Pydantic models for type-safe API responses
- SQLite database layer with aircraft and engine type mappings
- FAA data update script (`scripts/update_faa_data.py`)
  - Downloads FAA Releasable Aircraft Database
  - Parses MASTER.txt and ACFTREF.txt files
  - Builds optimized SQLite database (~25MB with ~300K records)
- Dark-themed web UI with:
  - Single lookup with real-time validation
  - Bulk lookup (paste multiple tail numbers)
  - Database statistics display
  - Responsive design
- Configuration files:
  - `.gitignore` - Excludes database files, Python cache, IDE files
  - `.dockerignore` - Optimizes Docker build context
  - `requirements.txt` - FastAPI, Uvicorn, Pydantic, httpx
- Docker support:
  - `Dockerfile` - Python 3.12-slim with baked-in database
  - `docker-compose.yml` - Simple deployment configuration
- GitHub Actions CI/CD:
  - `.github/workflows/nightly-build.yml` - Daily automated database updates at 6 AM UTC
  - `.github/workflows/build.yml` - Rebuild on code changes
  - Automatic Docker Hub publication
  - GitHub Releases for database snapshots
- Documentation:
  - `README.md` - Project documentation with examples
  - `CHANGELOG.md` - Version history tracking
  - `.github/SESSION_NOTES.md` - Development progress tracking
- GitHub repository templates:
  - `.github/ISSUE_TEMPLATE/` - Bug report and feature request templates
  - `.github/PULL_REQUEST_TEMPLATE.md` - PR template
  - `.github/CODEOWNERS` - Code ownership configuration
  - `renovate.json` - Automated dependency updates

### Technical Details
- Python 3.12 with FastAPI framework
- SQLite database with JOIN optimization
- CORS enabled for cross-origin requests
- Supports multiple N-number formats (N172SP, 172SP, N-172SP)
- Case-insensitive tail number lookup

## Project Structure
```
tail-lookup/
├── app/
│   ├── main.py           # FastAPI application
│   ├── database.py       # SQLite operations
│   ├── models.py         # Pydantic models
│   └── static/
│       └── index.html    # Web UI
├── scripts/
│   └── update_faa_data.py  # FAA data download/build script
├── data/                 # Database storage (gitignored)
├── .github/workflows/    # CI/CD (coming soon)
├── requirements.txt
└── CHANGELOG.md
```

---

## Version History

### Upcoming Releases

**v1.0.0** - Initial Release (Planned)
- Complete API implementation
- Docker image with baked-in database
- Automated nightly database updates
- Multi-architecture support (amd64, arm64, arm/v7)
- Docker Hub publication
