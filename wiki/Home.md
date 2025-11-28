# Tail Lookup Wiki

Welcome to the tail-lookup technical documentation. This wiki provides comprehensive information about the architecture, implementation, and operation of the FAA aircraft registration lookup API.

## Quick Links

- [Architecture Overview](Architecture-Overview)
- [Database Design](Database-Design)
- [API Documentation](API-Documentation)
- [Deployment Guide](Deployment-Guide)
- [CI/CD Pipeline](CI-CD-Pipeline)
- [Development Guide](Development-Guide)
- [Troubleshooting](Troubleshooting)

## Project Overview

Tail-lookup is a lightweight FastAPI-based service that provides aircraft registration data from the FAA Releasable Aircraft Database. The service is designed for:

- **Zero-configuration deployment** - Database baked into Docker image
- **Daily updates** - Automated nightly builds with latest FAA data
- **High performance** - SQLite with JOIN optimization
- **Developer-friendly** - OpenAPI/Swagger documentation, simple REST API
- **Production-ready** - Health checks, CORS support, multi-architecture Docker images

## Key Features

- Single and bulk aircraft lookup by N-number
- Supports multiple tail number formats (N172SP, 172SP, N-172SP)
- Dark-themed web UI for testing
- Automated database updates at 6 AM UTC daily
- Docker Hub publication with date-tagged releases
- GitHub Releases with database snapshots

## Technology Stack

- **Language**: Python 3.12
- **Framework**: FastAPI
- **Database**: SQLite
- **Server**: Uvicorn (ASGI)
- **Validation**: Pydantic
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Container Registry**: Docker Hub

## Repository Structure

```
tail-lookup/
├── app/                    # Application code
│   ├── main.py            # FastAPI application
│   ├── database.py        # Database operations
│   ├── models.py          # Pydantic models
│   └── static/
│       └── index.html     # Web UI
├── scripts/
│   └── update_faa_data.py # FAA data pipeline
├── data/                  # Database storage (gitignored)
├── .github/
│   └── workflows/         # CI/CD pipelines
├── wiki/                  # Documentation (synced to GitHub Wiki)
└── docker-compose.yml     # Deployment configuration
```

## Getting Started

### Quick Start with Docker

```bash
docker run -d -p 8080:8080 ryakel/tail-lookup:latest
```

### Local Development

```bash
# Build database
python scripts/update_faa_data.py data/aircraft.db

# Run API
DB_PATH=data/aircraft.db uvicorn app.main:app --reload --port 8080
```

See the [Development Guide](Development-Guide) for detailed setup instructions.

## Contributing

This project follows standard GitHub workflows:
- Issues and feature requests via GitHub Issues
- Pull requests for contributions
- Automated testing and building via GitHub Actions

See repository templates for issue and PR guidelines.
