# Troubleshooting

Common issues, solutions, and debugging strategies for tail-lookup.

## Common Issues

### API Issues

#### Aircraft Not Found (404)

**Symptom**: `GET /api/v1/aircraft/N12345` returns 404

**Possible Causes**:
1. Tail number not in FAA database (deregistered, never registered)
2. Tail number format incorrect
3. Database is stale or incomplete

**Solutions**:
```bash
# Verify tail number exists in FAA registry
https://registry.faa.gov/aircraftinquiry/Search/NNumberInquiry

# Check database has records
curl http://localhost:8080/api/v1/health

# Try different formats
curl http://localhost:8080/api/v1/aircraft/N12345
curl http://localhost:8080/api/v1/aircraft/12345

# Check database directly
sqlite3 data/aircraft.db "SELECT * FROM master WHERE n_number LIKE '12345%'"
```

#### Bulk Lookup Returns Errors

**Symptom**: Some results have `"error": "Not found"`

**This is expected behavior** - bulk endpoint doesn't fail if some tail numbers are invalid. Check individual results.

#### 422 Validation Error

**Symptom**: `422 Unprocessable Entity` response

**Causes**:
- Too many tail numbers in bulk request (>50)
- Invalid JSON format
- Wrong Content-Type header

**Solutions**:
```bash
# Check request format
curl -X POST http://localhost:8080/api/v1/aircraft/bulk \
  -H "Content-Type: application/json" \
  -d '{"tail_numbers": ["N172SP"]}'

# Ensure max 50 tail numbers
tail_numbers=($(head -50 file.txt))

# Verify JSON is valid
echo '{"tail_numbers": ["N172SP"]}' | jq
```

---

### Database Issues

#### Database File Not Found

**Symptom**: API fails to start with "database file not found"

**Solutions**:
```bash
# Local development - build database
python scripts/update_faa_data.py data/aircraft.db

# Docker - use official image (has database baked in)
docker pull ryakel/tail-lookup:latest

# Or download from releases
curl -L -o data/aircraft.db \
  https://github.com/ryakel/tail-lookup/releases/latest/download/aircraft.db
```

#### Zero Records in Database

**Symptom**: Health check shows `record_count: 0`

**Causes**:
- Database build failed
- FAA data format changed
- Parsing logic broken

**Solutions**:
```bash
# Check database file exists and has size
ls -lh data/aircraft.db

# Inspect database
sqlite3 data/aircraft.db "SELECT COUNT(*) FROM master"
sqlite3 data/aircraft.db "SELECT * FROM master LIMIT 5"

# Rebuild database
rm data/aircraft.db
python scripts/update_faa_data.py data/aircraft.db

# Check build script output for errors
python scripts/update_faa_data.py data/aircraft.db 2>&1 | tee build.log
```

#### Stale Database

**Symptom**: `last_updated` is more than 24 hours old

**Solutions**:
```bash
# Docker - pull latest image
docker pull ryakel/tail-lookup:latest
docker stop tail-lookup && docker rm tail-lookup
docker run -d --name tail-lookup -p 8080:8080 ryakel/tail-lookup:latest

# Local - rebuild database
python scripts/update_faa_data.py data/aircraft.db

# Check GitHub Actions for nightly build failures
https://github.com/ryakel/tail-lookup/actions/workflows/nightly-build.yml
```

---

### Docker Issues

#### Container Won't Start

**Symptom**: `docker run` exits immediately

**Diagnosis**:
```bash
# Check logs
docker logs tail-lookup

# Run interactively to see errors
docker run --rm -it -p 8080:8080 ryakel/tail-lookup:latest
```

**Common Causes**:
1. Port 8080 already in use
2. Database file missing in custom build
3. Python errors in application code

**Solutions**:
```bash
# Use different port
docker run -d --name tail-lookup -p 8081:8080 ryakel/tail-lookup:latest

# Verify database in image
docker run --rm ryakel/tail-lookup:latest ls -lh /app/data/aircraft.db

# Check image is official
docker pull ryakel/tail-lookup:latest
```

#### Health Check Failing

**Symptom**: `docker ps` shows "(unhealthy)"

**Diagnosis**:
```bash
# Check container health
docker inspect --format='{{json .State.Health}}' tail-lookup | jq

# Manual health check
docker exec tail-lookup curl -f http://localhost:8080/api/v1/health
```

**Solutions**:
- Wait for startup period (5 seconds)
- Check application logs: `docker logs tail-lookup`
- Verify database exists: `docker exec tail-lookup ls /app/data/`
- Restart container: `docker restart tail-lookup`

#### Can't Access API from Host

**Symptom**: `curl http://localhost:8080` fails with "Connection refused"

**Causes**:
1. Port not mapped correctly
2. Container not running
3. Firewall blocking connection

**Solutions**:
```bash
# Check container is running
docker ps

# Verify port mapping
docker port tail-lookup
# Should show: 8080/tcp -> 0.0.0.0:8080

# Check if process is listening
docker exec tail-lookup netstat -tuln | grep 8080

# Try from inside container
docker exec tail-lookup curl http://localhost:8080/api/v1/health
```

---

### CI/CD Issues

#### Nightly Build Not Running

**Symptom**: No builds in last 24 hours

**Causes**:
1. Repository inactive >60 days (GitHub disables)
2. Workflow file syntax error
3. GitHub Actions service issue

**Solutions**:
```bash
# Trigger manual run
gh workflow run nightly-build.yml

# Or via GitHub UI:
# Actions → Nightly Build → Run workflow

# Check workflow file syntax
cat .github/workflows/nightly-build.yml | yq

# Check GitHub status
https://www.githubstatus.com/
```

#### Docker Push Fails

**Symptom**: Workflow fails at "Build and push" step

**Error messages**:
- "unauthorized: authentication required"
- "denied: requested access to the resource is denied"

**Solutions**:
```bash
# Verify secrets are set
# GitHub: Settings → Secrets and variables → Actions
# Required: DOCKERHUB_USERNAME, DOCKERHUB_TOKEN

# Regenerate Docker Hub token
# https://hub.docker.com/settings/security
# Create new token with Read & Write permissions

# Update repository secret with new token
```

#### Release Not Created

**Symptom**: No GitHub Release after nightly build

**Causes**:
- `contents: write` permission missing
- Release step failed
- Tag already exists

**Solutions**:
```bash
# Check workflow permissions
cat .github/workflows/nightly-build.yml | grep -A 5 permissions

# View workflow logs for release step
# Actions → Latest run → Update GitHub Release

# Delete existing tag if conflict
git push origin :refs/tags/data-2025-11-28
```

---

### Development Issues

#### Import Errors

**Symptom**: `ModuleNotFoundError` when running locally

**Solutions**:
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
```

#### Server Won't Start

**Symptom**: `uvicorn app.main:app` fails

**Common Errors**:
1. "No module named 'app'"
2. "Database file not found"
3. "Address already in use"

**Solutions**:
```bash
# Error 1: Run from project root
cd /path/to/tail-lookup
uvicorn app.main:app --reload

# Error 2: Set DB_PATH
export DB_PATH=data/aircraft.db
python scripts/update_faa_data.py data/aircraft.db

# Error 3: Use different port
uvicorn app.main:app --reload --port 8081

# Or kill existing process
lsof -ti:8080 | xargs kill -9
```

#### Auto-reload Not Working

**Symptom**: Code changes don't reflect without manual restart

**Solutions**:
- Ensure using `--reload` flag
- Check file is being saved
- Try restarting server manually
- Verify you're editing correct file (not cached copy)

---

### Performance Issues

#### Slow API Responses

**Symptom**: Requests take >1 second

**Normal Performance**:
- Single lookup: 1-5ms
- Bulk (50): 5-20ms
- Health check: <1ms

**Diagnosis**:
```bash
# Time a request
time curl http://localhost:8080/api/v1/aircraft/N172SP

# Check database size
du -h data/aircraft.db  # Should be ~25MB

# Verify index exists
sqlite3 data/aircraft.db ".indices master"
# Should include: idx_mfr_mdl_code
```

**Solutions**:
- Rebuild database (index might be missing)
- Check system resources (CPU, RAM, disk I/O)
- Verify database file isn't corrupted
- Restart application

#### High Memory Usage

**Normal**: 100-200MB RAM

**High**: >500MB RAM

**Diagnosis**:
```bash
# Docker
docker stats tail-lookup

# Local process
ps aux | grep uvicorn
```

**Solutions**:
- Restart application
- Check for memory leaks in custom code
- Update to latest image/code
- Increase container memory limit if needed

---

### Network Issues

#### CORS Errors in Browser

**Symptom**: "No 'Access-Control-Allow-Origin' header" in browser console

**Current behavior**: CORS is enabled for all origins

**If you added CORS restrictions**:
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Add your domain
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Can't Access from External IP

**Symptom**: API works on localhost but not from other machines

**Solutions**:
```bash
# Verify server is listening on 0.0.0.0 (not 127.0.0.1)
uvicorn app.main:app --host 0.0.0.0 --port 8080

# Check firewall
# Allow port 8080
sudo ufw allow 8080/tcp  # Linux
# Or configure firewall in cloud provider console

# Verify with:
curl http://<external-ip>:8080/api/v1/health
```

---

## Debugging Strategies

### Enable Debug Logging

```python
# Add to app/main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Inspect Requests/Responses

```bash
# Verbose curl
curl -v http://localhost:8080/api/v1/aircraft/N172SP

# Use httpx for debugging
python -c "
import httpx
response = httpx.get('http://localhost:8080/api/v1/aircraft/N172SP')
print(f'Status: {response.status_code}')
print(f'Headers: {response.headers}')
print(f'Body: {response.text}')
"
```

### Check Database Contents

```bash
# Open database
sqlite3 data/aircraft.db

# Useful queries
SELECT COUNT(*) FROM master;
SELECT COUNT(*) FROM acftref;
SELECT * FROM master WHERE n_number = '172SP';
SELECT * FROM metadata;
.schema
.quit
```

### Monitor Application

```bash
# Docker logs (live)
docker logs -f --tail=100 tail-lookup

# Process monitoring
top -p $(pgrep -f uvicorn)

# Network monitoring
netstat -tuln | grep 8080
```

---

## Getting Help

1. **Check this troubleshooting guide** - Most issues covered here
2. **Search existing issues**: https://github.com/ryakel/tail-lookup/issues
3. **Check workflow logs**: https://github.com/ryakel/tail-lookup/actions
4. **Create new issue**: https://github.com/ryakel/tail-lookup/issues/new
5. **Discussions**: https://github.com/ryakel/tail-lookup/discussions

### Information to Include

When reporting issues, include:
- Operating system and version
- Python version (`python --version`)
- Docker version (`docker --version`)
- Error messages (full output)
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs

### Example Issue

```markdown
**Describe the bug**
API returns 500 error for specific tail number N12345

**To Reproduce**
1. Run: `curl http://localhost:8080/api/v1/aircraft/N12345`
2. See error: {"detail": "Internal server error"}

**Expected behavior**
Should return aircraft data or 404 if not found

**Environment**
- OS: macOS 14.1
- Python: 3.12.0
- Docker: 24.0.6
- Image: ryakel/tail-lookup:2025-11-28

**Logs**
```
[Include relevant logs here]
```

**Database**
```
Record count: 297431
Last updated: 2025-11-28T06:15:23Z
```
```

---

## References

- [FastAPI Debugging](https://fastapi.tiangolo.com/tutorial/debugging/)
- [Docker Troubleshooting](https://docs.docker.com/config/containers/troubleshooting/)
- [SQLite Troubleshooting](https://www.sqlite.org/faq.html)
- [GitHub Actions Debugging](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/enabling-debug-logging)
