# tail-lookup

[![Docker Pulls](https://img.shields.io/docker/pulls/ryakel/tail-lookup)](https://hub.docker.com/r/ryakel/tail-lookup)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/v/release/ryakel/tail-lookup)](https://github.com/ryakel/tail-lookup/releases)

Lightweight, self-hosted API for FAA aircraft registration lookup by N-number.

Database baked into image—just pull and run.

## Quick Start

```bash
docker run -d -p 8182:8080 ryakel/tail-lookup:latest
```

Open http://localhost:8182 for the web UI, or use the API directly:

```bash
curl http://localhost:8182/api/v1/aircraft/N172SP
```

## Features

- 🔍 Single and bulk lookups (up to 50 at once)
- 🌐 Simple web UI for testing
- 📦 ~25MB SQLite database with ~300k aircraft
- 🔄 Nightly automated updates via GitHub Actions
- 🐳 Zero-config Docker deployment

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/api/v1/aircraft/{tail}` | GET | Single lookup |
| `/api/v1/aircraft/bulk` | POST | Bulk lookup (max 50) |
| `/api/v1/health` | GET | Health + data freshness |
| `/api/v1/stats` | GET | Record count, last update |
| `/docs` | GET | OpenAPI documentation |

### Single Lookup

```bash
curl http://localhost:8182/api/v1/aircraft/N172SP
```

```json
{
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
```

All formats accepted: `N172SP`, `172SP`, `N-172SP`, `n172sp`

### Bulk Lookup

```bash
curl -X POST http://localhost:8182/api/v1/aircraft/bulk \
  -H "Content-Type: application/json" \
  -d '{"tail_numbers": ["N172SP", "N12345", "N99999"]}'
```

```json
{
  "total": 3,
  "found": 2,
  "results": [
    {
      "tail_number": "N172SP",
      "manufacturer": "CESSNA",
      "model": "172S",
      ...
    },
    {
      "tail_number": "N12345",
      "manufacturer": "PIPER",
      ...
    },
    {
      "tail_number": "N99999",
      "error": "Not found"
    }
  ]
}
```

## Image Tags

| Tag | Description |
|-----|-------------|
| `:latest` | Most recent nightly build |
| `:2025-11-28` | Pin to specific date |

New images built daily at 6 AM UTC with fresh FAA data.

## Deploy with flight-budget

```yaml
version: "3.8"

services:
  flight-budget:
    image: ryakel/flight-budget:latest
    ports:
      - "8181:80"

  tail-lookup:
    image: ryakel/tail-lookup:latest
    ports:
      - "8182:8080"
```

## Documentation

For comprehensive documentation, see the [GitHub Wiki](https://github.com/ryakel/tail-lookup/wiki):

- **[Architecture Overview](https://github.com/ryakel/tail-lookup/wiki/Architecture-Overview)** - System design and data flow
- **[Database Design](https://github.com/ryakel/tail-lookup/wiki/Database-Design)** - Schema, FAA data format, optimization
- **[API Documentation](https://github.com/ryakel/tail-lookup/wiki/API-Documentation)** - Complete API reference with examples
- **[Deployment Guide](https://github.com/ryakel/tail-lookup/wiki/Deployment-Guide)** - Docker, Kubernetes, cloud platforms
- **[CI/CD Pipeline](https://github.com/ryakel/tail-lookup/wiki/CI-CD-Pipeline)** - Workflow documentation and secrets
- **[Development Guide](https://github.com/ryakel/tail-lookup/wiki/Development-Guide)** - Local setup and contribution guidelines
- **[Troubleshooting](https://github.com/ryakel/tail-lookup/wiki/Troubleshooting)** - Common issues and solutions

## Development

```bash
# Clone
git clone https://github.com/ryakel/tail-lookup.git
cd tail-lookup

# Build database locally
python scripts/update_faa_data.py data/aircraft.db

# Run
pip install -r requirements.txt
DB_PATH=data/aircraft.db uvicorn app.main:app --reload --port 8080
```

See the [Development Guide](https://github.com/ryakel/tail-lookup/wiki/Development-Guide) for complete setup instructions.

## Data Source

Aircraft data from [FAA Releasable Aircraft Database](https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download), updated daily at 11:30 PM CT.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Inspired by [Aircraft-Registration-Lookup-API](https://github.com/njfdev/Aircraft-Registration-Lookup-API)
- Data: [FAA Aircraft Registry](https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry)
