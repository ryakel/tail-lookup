# Changelog

All notable changes to tail-lookup are documented here.

## Latest Changes

### Automated Release System (2025-11-28)
- **Automatic releases on main branch merges**: Creates GitHub releases when PRs from develop are merged
- **Semantic versioning**: Automatic version bumping based on commit message conventions
  - `breaking:` or `major:` → Major version bump (x.0.0)
  - `feat:` or `feature:` → Minor version bump (0.x.0)
  - All other commits → Patch version bump (0.0.x)
- **Database artifact upload**: Each release includes downloadable `aircraft.db` file
- **Database statistics**: Record count and last updated timestamp in release notes
- **Release notes generation**: Automatically extracts recent changes from this changelog
- **Docker image tagging**: Images tagged with both date and version number
- **Comprehensive release documentation**: Created [Release Process](Release-Process) guide

### Cross-Project Integration Support (2025-11-28)
- **Integration framework established**: API can be used as a microservice by other applications
- **FAA lookup capability**: Aircraft data can be retrieved during data import/processing workflows
- **Docker Compose compatibility**: Example configurations available for multi-service deployments
- **Documentation standardized**: API documentation and deployment guides support integration scenarios
- **Future-ready**: Architecture supports planned consolidation into TrueHour unified platform

### Database Parsing Bug Fix (2025-11-28)
- **Fixed NO-ENG and NO-SEATS parsing**: Added missing columns to MASTER.txt parser
- **Improved data accuracy**: COALESCE prefers ACFTREF (reference) data over MASTER data
- **Verified results**: N55350 now shows 1 engine, 4 seats (was showing 4 engines, null seats)
- **Better data quality**: More accurate information for all aircraft

### Build Performance Optimization (2025-11-28)
- **Parallelized multi-architecture builds** using GitHub Actions matrix strategy
- **3x faster builds**: ~15 minutes (down from 45+ minutes)
- Split workflows into prepare-database, build (parallel), and merge jobs
- Build each platform separately using push-by-digest strategy
- Merge platform images into single multi-platform manifest
- Per-platform cache scoping for better efficiency
- Applied to: `build-main.yml`, `build-develop.yml`, `nightly-build.yml`

### Platform Support Changes (2025-11-28)
- **Dropped ARM v7 support** from all workflows (too slow, rarely used)
- Kept `linux/amd64` and `linux/arm64` (most common platforms)
- Updated all documentation to remove arm/v7 references

## Core Features

### FAA Aircraft Lookup API
- FastAPI-based REST API with 5 endpoints
- Single aircraft lookup (`GET /api/v1/aircraft/{tail}`)
- Bulk aircraft lookup (`POST /api/v1/aircraft/bulk`)
- Health check endpoint (`GET /api/v1/health`)
- Database statistics endpoint (`GET /api/v1/stats`)
- Web UI for interactive lookups (`GET /`)

### Database
- SQLite database with ~300K FAA aircraft registrations
- Parsed from FAA ReleasableAircraft database
- MASTER.txt (main registration data)
- ACFTREF.txt (reference data for accurate specifications)
- Automatic daily updates via nightly builds
- Database baked into Docker image (zero-configuration)

### Docker & CI/CD
- Multi-architecture Docker images (amd64, arm64)
- Automated nightly builds with fresh FAA data
- GitHub Actions workflows for develop and main branches
- Release automation with semantic versioning
- Docker Hub automatic deployment

### Integration
- Microservice architecture for integration with other applications
- Nginx reverse proxy support
- Profile-based conditional deployment
- Internal Docker networking
- Health check support for service orchestration

## Related Documentation

- [Release Process](Release-Process) - How releases are created
- [CI/CD Pipeline](CI-CD-Pipeline) - Build and deployment workflows
- [API Documentation](API-Documentation) - REST API endpoints
- [Database Design](Database-Design) - Database schema and structure
- [Deployment Guide](Deployment-Guide) - Production deployment

---

**Note**: This changelog is used to generate release notes when PRs are merged from develop to main. Keep it up to date with all changes!
