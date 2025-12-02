# Development Guide

Guide for developers working on tail-lookup, including local setup, development workflow, testing, and contribution guidelines.

## Prerequisites

- Python 3.12+
- Git
- Docker (optional, for testing container builds)
- curl or httpx (for testing API)

## Local Development Setup

### 1. Clone Repository

```bash
git clone git@github.com:ryakel/tail-lookup.git
cd tail-lookup
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3.12 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Build Database

```bash
# Download and build FAA database (~30 seconds)
python scripts/update_faa_data.py data/aircraft.db
```

Expected output:
```
Downloading FAA data...
Parsing MASTER.txt...
Parsing ACFTREF.txt...
Building database...
Database created successfully!
Records: 297431
Size: 24.5 MB
```

### 4. Run API Server

```bash
# Set database path (required)
export DB_PATH=data/aircraft.db

# Run with auto-reload for development
uvicorn app.main:app --reload --port 8080
```

Server starts at: http://localhost:8080

### 5. Test API

```bash
# Health check
curl http://localhost:8080/api/v1/health

# Single lookup
curl http://localhost:8080/api/v1/aircraft/N172SP

# Bulk lookup
curl -X POST http://localhost:8080/api/v1/aircraft/bulk \
  -H "Content-Type: application/json" \
  -d '{"tail_numbers": ["N172SP", "N12345"]}'

# Web UI
open http://localhost:8080
```

---

## Project Structure

```
tail-lookup/
├── app/                    # Application code
│   ├── main.py            # FastAPI app, routes, middleware
│   ├── database.py        # SQLite operations, type mappings
│   ├── models.py          # Pydantic request/response models
│   └── static/
│       └── index.html     # Web UI
├── scripts/
│   └── update_faa_data.py # FAA data download and database build
├── data/                  # Database storage (gitignored)
│   └── aircraft.db        # SQLite database (not in repo)
├── wiki/                  # Documentation (synced to GitHub Wiki)
├── .github/
│   ├── workflows/         # CI/CD pipelines
│   └── ISSUE_TEMPLATE/    # Issue templates
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container image
├── docker-compose.yml     # Simple deployment
└── README.md             # Project overview
```

---

## Development Workflow

### Making Changes

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**:
   - Edit code in `app/`
   - Server auto-reloads with `--reload` flag
   - Test changes locally

3. **Update documentation**:
   - Update `wiki/Changelog.md` with changes
   - Update relevant wiki pages if needed
   - Update API docs in code (docstrings)

4. **Test changes**:
   ```bash
   # Test manually
   curl http://localhost:8080/api/v1/aircraft/N172SP

   # Or use Python
   python -c "import httpx; print(httpx.get('http://localhost:8080/api/v1/aircraft/N172SP').json())"
   ```

5. **Commit changes**:
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

6. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

   Then create Pull Request on GitHub.

### Code Style

**Python**:
- Follow PEP 8 style guide
- Use type hints (Python 3.12+)
- Docstrings for functions and classes
- Keep functions small and focused

**Example**:
```python
def normalize_tail(tail: str) -> str:
    """Normalize N-number to standard format.

    Args:
        tail: Raw tail number (e.g., "N172SP", "n-172sp")

    Returns:
        Normalized tail number (e.g., "172SP")

    Examples:
        >>> normalize_tail("N172SP")
        "172SP"
        >>> normalize_tail("n-172sp")
        "172SP"
    """
    t = tail.upper().strip()
    if t.startswith("N"):
        t = t[1:]
    return t.replace("-", "").replace(" ", "")
```

### Testing Locally

**Manual testing**:
```bash
# Single lookup
curl http://localhost:8080/api/v1/aircraft/N172SP | jq

# Bulk lookup
curl -X POST http://localhost:8080/api/v1/aircraft/bulk \
  -H "Content-Type: application/json" \
  -d '{"tail_numbers": ["N172SP", "N12345", "N99999"]}' | jq

# Health check
curl http://localhost:8080/api/v1/health | jq

# Stats
curl http://localhost:8080/api/v1/stats | jq

# Web UI
open http://localhost:8080

# OpenAPI docs
open http://localhost:8080/docs
```

**Database queries**:
```bash
# Check record count
sqlite3 data/aircraft.db "SELECT COUNT(*) FROM master"

# Sample records
sqlite3 data/aircraft.db "SELECT * FROM master LIMIT 5"

# Check last updated
sqlite3 data/aircraft.db "SELECT value FROM metadata WHERE key='last_updated'"
```

---

## Building and Testing Docker Image

### Local Docker Build

```bash
# Build database first
python scripts/update_faa_data.py data/aircraft.db

# Build Docker image
docker build -t tail-lookup:dev .

# Run container
docker run -d --name tail-lookup-dev -p 8080:8080 tail-lookup:dev

# Test
curl http://localhost:8080/api/v1/health

# View logs
docker logs -f tail-lookup-dev

# Stop and remove
docker stop tail-lookup-dev
docker rm tail-lookup-dev
```

### Testing with Docker Compose

```bash
# Build and start
docker compose up --build -d

# View logs
docker compose logs -f

# Test
curl http://localhost:8080/api/v1/health

# Stop
docker compose down
```

---

## Debugging

### Python Debugger

Add breakpoint in code:
```python
import pdb; pdb.set_trace()
```

Then run with debugger attached.

### Print Debugging

Add logging:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"Looking up tail: {tail_number}")
```

### Database Debugging

```bash
# Open database in interactive mode
sqlite3 data/aircraft.db

# Run queries
SELECT * FROM master WHERE n_number = '172SP';
SELECT * FROM acftref WHERE code = '0550264';
.tables
.schema master
.quit
```

---

## Common Tasks

### Update FAA Data

```bash
# Download and rebuild database
python scripts/update_faa_data.py data/aircraft.db

# Restart server (if running)
# Server will pick up new database
```

### Add New Endpoint

1. **Define Pydantic model** in `app/models.py`:
   ```python
   class MyResponse(BaseModel):
       field1: str
       field2: int
   ```

2. **Add route** in `app/main.py`:
   ```python
   @app.get("/api/v1/myendpoint", response_model=MyResponse)
   async def my_endpoint():
       return MyResponse(field1="value", field2=42)
   ```

3. **Test**:
   ```bash
   curl http://localhost:8080/api/v1/myendpoint
   ```

4. **Update docs**:
   - Add to `wiki/API-Documentation.md`
   - Update `wiki/Changelog.md`

### Modify Database Schema

**Not recommended** - would require changes to:
1. `scripts/update_faa_data.py` - Schema creation
2. `app/database.py` - Query logic
3. `app/models.py` - Response models
4. All consumers of API

Better: Add new fields as optional in models.

### Change Type Mappings

Edit `app/database.py`:
```python
AIRCRAFT_TYPES = {
    "1": "Glider",
    "2": "Balloon",
    # Add new mapping
    "12": "New Type",
}
```

---

## Contribution Guidelines

### Pull Request Process

1. **Fork repository** (for external contributors)
2. **Create feature branch**
3. **Make changes** with tests
4. **Update documentation** (wiki/Changelog.md, other wiki pages)
5. **Commit with descriptive message**
6. **Push to your fork/branch**
7. **Create Pull Request** with description
8. **Address review feedback**
9. **Wait for approval and merge**

### PR Description Template

See `.github/PULL_REQUEST_TEMPLATE.md`

### Commit Message Format

```
<type>: <short description>

<detailed description if needed>

<footer: references issues, breaking changes, etc.>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance tasks (dependencies, build)

**Examples**:
```
feat: Add search endpoint for manufacturer lookup

Implements new /api/v1/search endpoint that allows searching
aircraft by manufacturer name. Includes pagination support.

Closes #42
```

```
fix: Handle missing year_mfr in database

Some aircraft records don't have year_mfr field. Updated
database.py to handle None values gracefully.

Fixes #38
```

---

## Troubleshooting Development Issues

### "Module not found" errors

```bash
# Ensure dependencies installed
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.12+

# Activate virtual environment
source .venv/bin/activate
```

### "Database file not found"

```bash
# Build database
python scripts/update_faa_data.py data/aircraft.db

# Set DB_PATH environment variable
export DB_PATH=data/aircraft.db
```

### "Port already in use"

```bash
# Find process using port 8080
lsof -i :8080  # Mac/Linux
netstat -ano | findstr :8080  # Windows

# Kill process or use different port
uvicorn app.main:app --reload --port 8081
```

### "FAA download fails"

```bash
# Check FAA website is accessible
curl -I https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download

# Use cached database from releases
curl -L -o data/aircraft.db https://github.com/ryakel/tail-lookup/releases/latest/download/aircraft.db
```

---

## IDE Setup

### VS Code

**Recommended extensions**:
- Python (Microsoft)
- Pylance (Microsoft)
- autoDocstring (Nils Werner)
- Better Comments (Aaron Bond)

**.vscode/settings.json**:
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".venv": true,
    "data/": true
  }
}
```

### PyCharm

1. Open project
2. Configure Python interpreter: .venv/bin/python
3. Mark `app/` as Sources Root
4. Enable FastAPI support in settings

---

## Resources

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLite Python](https://docs.python.org/3/library/sqlite3.html)
- [FAA Data Format](https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

---

## Getting Help

- **Issues**: https://github.com/ryakel/tail-lookup/issues
- **Discussions**: https://github.com/ryakel/tail-lookup/discussions
- **Wiki**: https://github.com/ryakel/tail-lookup/wiki
