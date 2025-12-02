# CI/CD Pipeline

Comprehensive documentation of the tail-lookup CI/CD workflows, automation, and deployment processes.

## Overview

Tail-lookup uses GitHub Actions for automated builds, testing, and deployment. The CI/CD pipeline consists of three main workflows:

1. **Nightly Build** - Daily automated database updates
2. **Main Branch Build** - Builds triggered by code changes to main, with versioning and releases
3. **Develop Branch Build** - Builds triggered by code changes to develop branch

All workflows build Docker images and publish to Docker Hub with appropriate tagging.

## Workflows

### 1. Nightly Build Workflow

**File**: `.github/workflows/nightly-build.yml`
**Purpose**: Daily automated FAA database updates
**Schedule**: Daily at 6:00 AM UTC (cron: `0 6 * * *`)
**Trigger**: Schedule or manual dispatch

#### Workflow Steps

```yaml
name: Nightly Build

on:
  schedule:
    - cron: '0 6 * * *'  # 6 AM UTC daily
  workflow_dispatch:      # Allow manual trigger

permissions:
  contents: write         # For creating releases
  packages: write         # For publishing Docker images

env:
  REGISTRY: docker.io
  IMAGE_NAME: ryakel/tail-lookup
```

**Step 1: Checkout repository**
```yaml
- name: Checkout repository
  uses: actions/checkout@v4
```
- Checks out code from main branch
- Required for accessing build scripts

**Step 2: Set up Python**
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
```
- Installs Python 3.12 (matches production)
- Used for running database build script

**Step 3: Download and build database**
```yaml
- name: Download and build database
  run: |
    python scripts/update_faa_data.py data/aircraft.db
```
- Downloads ReleasableAircraft.zip from FAA (~30MB)
- Parses MASTER.txt and ACFTREF.txt
- Builds SQLite database (~25MB)
- Takes ~30-45 seconds

**Step 4: Get build info**
```yaml
- name: Get build info
  id: info
  run: |
    RECORDS=$(sqlite3 data/aircraft.db "SELECT COUNT(*) FROM master")
    SIZE=$(du -h data/aircraft.db | cut -f1)
    DATE=$(date -u +%Y-%m-%d)
    echo "records=$RECORDS" >> $GITHUB_OUTPUT
    echo "size=$SIZE" >> $GITHUB_OUTPUT
    echo "date=$DATE" >> $GITHUB_OUTPUT
```
- Queries database for record count
- Gets database file size
- Generates date string for tagging
- Outputs used in subsequent steps

**Step 5: Set up Docker Buildx**
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
```
- Enables advanced Docker build features
- Required for caching and multi-platform builds

**Step 6: Log in to Docker Hub**
```yaml
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```
- Authenticates with Docker Hub
- Uses repository secrets for credentials
- Required for pushing images

**Step 7: Build and push Docker image**
```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: |
      ${{ env.IMAGE_NAME }}:latest
      ${{ env.IMAGE_NAME }}:${{ steps.info.outputs.date }}
    labels: |
      org.opencontainers.image.title=tail-lookup
      org.opencontainers.image.description=FAA Aircraft Registration Lookup API
      org.opencontainers.image.created=${{ steps.info.outputs.date }}
      org.opencontainers.image.source=https://github.com/ryakel/tail-lookup
      faa.data.records=${{ steps.info.outputs.records }}
      faa.data.date=${{ steps.info.outputs.date }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```
- Builds Docker image with fresh database
- Tags with `latest` and date (e.g., `2025-11-28`)
- Adds metadata labels for tracking
- Uses GitHub Actions cache for faster builds

**Step 8: Create GitHub Release**
```yaml
- name: Update GitHub Release
  uses: softprops/action-gh-release@v2
  with:
    tag_name: data-${{ steps.info.outputs.date }}
    name: "FAA Data - ${{ steps.info.outputs.date }}"
    body: |
      ## FAA Aircraft Registration Database

      **Date:** ${{ steps.info.outputs.date }}
      **Records:** ${{ steps.info.outputs.records }}
      **DB Size:** ${{ steps.info.outputs.size }}

      **Docker Image:**
      ```
      docker pull ryakel/tail-lookup:${{ steps.info.outputs.date }}
      docker pull ryakel/tail-lookup:latest
      ```

      Source: [FAA Releasable Aircraft Database](https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download)
    files: data/aircraft.db
    prerelease: false
```
- Creates GitHub Release with database file
- Tags release with date (e.g., `data-2025-11-28`)
- Includes metadata (record count, size)
- Provides Docker pull commands
- Attaches database file for manual download

**Step 9: Trigger Portainer webhook (optional)**
```yaml
- name: Trigger Portainer webhook (optional)
  continue-on-error: true
  env:
    WEBHOOK_URL: ${{ secrets.PORTAINER_WEBHOOK_URL }}
  run: |
    if [ -n "$WEBHOOK_URL" ]; then
      curl -X POST "$WEBHOOK_URL"
    fi
```
- Optional webhook for automatic deployment
- Triggers Portainer to pull latest image
- Continues even if webhook not configured
- No failure if webhook URL not set

**Step 10: Build summary**
```yaml
- name: Summary
  run: |
    echo "## Build Complete 🎉" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "| Metric | Value |" >> $GITHUB_STEP_SUMMARY
    echo "|--------|-------|" >> $GITHUB_STEP_SUMMARY
    echo "| Date | ${{ steps.info.outputs.date }} |" >> $GITHUB_STEP_SUMMARY
    echo "| Records | ${{ steps.info.outputs.records }} |" >> $GITHUB_STEP_SUMMARY
    echo "| DB Size | ${{ steps.info.outputs.size }} |" >> $GITHUB_STEP_SUMMARY
    echo "| Image | \`${{ env.IMAGE_NAME }}:${{ steps.info.outputs.date }}\` |" >> $GITHUB_STEP_SUMMARY
```
- Creates formatted summary in GitHub Actions UI
- Shows key metrics from build
- Helps track builds over time

#### Timing and Schedule

**Why 6 AM UTC?**
- FAA updates data daily at 11:30 PM CT (5:30 AM UTC)
- 30-minute buffer ensures data is ready
- Low traffic time minimizes impact on users

**Manual Trigger**:
- Available via GitHub Actions UI
- Useful for testing or immediate updates
- No schedule required

#### Secrets Required

1. **DOCKERHUB_USERNAME**: Docker Hub username
   - Navigate to: Repository Settings → Secrets and variables → Actions
   - Add new repository secret

2. **DOCKERHUB_TOKEN**: Docker Hub access token
   - Generate at: https://hub.docker.com/settings/security
   - Use personal access token, not password
   - Add as repository secret

3. **PORTAINER_WEBHOOK_URL** (optional): Portainer webhook URL
   - Configure in Portainer service settings
   - Format: `https://portainer.example.com/api/webhooks/<id>`
   - Workflow continues if not set

---

### 2. Main Branch Build Workflow

**File**: `.github/workflows/build-main.yml`
**Purpose**: Build, version, and publish on code changes to main branch
**Trigger**: Push to main or PR to main (for paths: `app/**`, `Dockerfile`, `requirements.txt`)
**Note**: This workflow also handles semantic versioning and release creation

#### Workflow Steps

```yaml
name: Build on Code Change

on:
  push:
    branches: [main]
    paths:
      - 'app/**'
      - 'Dockerfile'
      - 'requirements.txt'
  pull_request:
    branches: [main]

permissions:
  contents: read          # Read code
  packages: write         # Publish Docker images

env:
  REGISTRY: docker.io
  IMAGE_NAME: ryakel/tail-lookup
```

**Step 1: Checkout repository**
- Same as nightly build

**Step 2: Download latest database from releases**
```yaml
- name: Download latest database from releases
  run: |
    mkdir -p data
    # Get latest release with aircraft.db
    DOWNLOAD_URL=$(curl -s https://api.github.com/repos/ryakel/tail-lookup/releases/latest \
      | jq -r '.assets[] | select(.name == "aircraft.db") | .browser_download_url')

    if [ -z "$DOWNLOAD_URL" ] || [ "$DOWNLOAD_URL" = "null" ]; then
      echo "No existing database found, building fresh..."
      pip install -q requests
      python scripts/update_faa_data.py data/aircraft.db
    else
      echo "Downloading from $DOWNLOAD_URL"
      curl -L -o data/aircraft.db "$DOWNLOAD_URL"
    fi
```
- Reuses latest database from GitHub Releases
- Avoids rebuilding database unnecessarily
- Falls back to fresh build if no release exists
- Speeds up build time significantly

**Step 3-5: Docker setup and login**
- Same as nightly build

**Step 6: Get metadata**
```yaml
- name: Get metadata
  id: meta
  run: |
    DATE=$(date -u +%Y-%m-%d)
    SHA=$(echo ${{ github.sha }} | cut -c1-7)
    echo "date=$DATE" >> $GITHUB_OUTPUT
    echo "sha=$SHA" >> $GITHUB_OUTPUT
```
- Generates date and short SHA for tagging
- Format: `2025-11-28-abc1234`
- Allows tracking specific code versions

**Step 7: Build and push**
```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: ${{ github.event_name != 'pull_request' }}
    tags: |
      ${{ env.IMAGE_NAME }}:latest
      ${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.date }}-${{ steps.meta.outputs.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```
- Builds with downloaded database
- Only pushes on main branch (not PRs)
- Tags with `latest` and `date-sha`
- Uses GitHub Actions cache

**Step 8: Trigger Portainer webhook (optional)**
- Same as nightly build
- Only runs on main branch

#### Path Filtering

**Trigger on changes to**:
- `app/**` - Application code changes
- `Dockerfile` - Container changes
- `requirements.txt` - Dependency changes

**Does NOT trigger on**:
- Documentation changes (`*.md`, `wiki/**`)
- CI/CD workflow changes (`.github/workflows/**`)
- Configuration changes (`.gitignore`, etc.)

This prevents unnecessary builds for non-code changes.

---

### 3. Develop Branch Build Workflow

**File**: `.github/workflows/build-develop.yml`
**Purpose**: Build and publish on code changes to develop branch
**Trigger**: Push to develop branch (for paths: `app/**`, `Dockerfile`, `requirements.txt`)

This workflow is similar to the main branch build but:
- Does NOT create releases or version tags
- Tags images with `develop` and `develop-YYYY-MM-DD-SHA` tags
- Used for testing before merging to main
- No automatic version bumping

---

## Docker Image Details

### Image Tags

**latest**:
- Always points to most recent main branch build
- Updated by nightly and main branch workflows
- Use for production deployments that want automatic updates

**develop**:
- Points to most recent develop branch build
- Updated by develop branch workflow
- Use for testing unreleased features

**Date tags** (e.g., `2025-11-28`):
- Created by nightly build
- Immutable snapshot of database on that date
- Use for reproducible deployments

**Date-SHA tags** (e.g., `2025-11-28-abc1234`):
- Created by main and develop branch builds
- Tracks specific code version with date
- Use for testing or rollback scenarios

**Version tags** (e.g., `v1.2.3`):
- Created by main branch build when creating releases
- Follows semantic versioning
- Use for pinning to specific release versions

### Image Labels

Images include OCI-compliant labels:
- `org.opencontainers.image.title` - Project name
- `org.opencontainers.image.description` - Project description
- `org.opencontainers.image.created` - Build date
- `org.opencontainers.image.source` - GitHub repository URL
- `faa.data.records` - Number of aircraft records (custom label)
- `faa.data.date` - Database date (custom label)

View labels:
```bash
docker inspect ryakel/tail-lookup:latest | jq '.[0].Config.Labels'
```

### Image Size

- Base image: `python:3.12-slim` (~150MB)
- Application code: ~10KB
- Dependencies: ~50MB (FastAPI, Uvicorn, Pydantic)
- Database: ~25MB
- **Total: ~225MB**

### Multi-Architecture Support

**Current**: Single architecture (amd64)
**Planned**: Multi-platform builds (amd64, arm64)

To enable:
```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
    # ... rest of config
```

---

## GitHub Releases

### Release Format

**Tag**: `data-YYYY-MM-DD` (e.g., `data-2025-11-28`)
**Title**: "FAA Data - YYYY-MM-DD"
**Body**: Formatted markdown with metadata and Docker pull commands
**Assets**: `aircraft.db` file (~25MB)

### Release Purpose

1. **Database snapshots**: Downloadable database files
2. **Version tracking**: Historical record of database updates
3. **Reuse by workflows**: Code change builds download latest database
4. **Manual access**: Users can download database without Docker

### Accessing Releases

**Latest release**:
```bash
curl -s https://api.github.com/repos/ryakel/tail-lookup/releases/latest | jq
```

**Download database**:
```bash
curl -L -o aircraft.db https://github.com/ryakel/tail-lookup/releases/latest/download/aircraft.db
```

**List all releases**:
```bash
curl -s https://api.github.com/repos/ryakel/tail-lookup/releases | jq '.[].tag_name'
```

---

## Caching Strategy

### GitHub Actions Cache

Both workflows use GitHub Actions cache for Docker builds:

```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

**Benefits**:
- Faster builds (reuse unchanged layers)
- Reduced bandwidth usage
- Automatic cleanup (old cache purged)

**Cache Contents**:
- Docker layer cache (Python packages, OS packages)
- Not the database (changes daily)

**Cache Performance**:
- Cold build: ~3 minutes
- Cached build: ~1 minute
- Database build: ~30 seconds

### Database Reuse

Code change workflow reuses databases from releases:
- Avoids 30-second FAA download + parse
- Ensures consistency with nightly builds
- Falls back to fresh build if needed

---

## Monitoring and Debugging

### Workflow Logs

**View in GitHub UI**:
1. Navigate to repository
2. Click "Actions" tab
3. Select workflow run
4. Click on step to see logs

**Download logs**:
```bash
gh run list --workflow=nightly-build.yml
gh run view <run-id> --log
```

### Common Issues

**Build fails on FAA download**:
- FAA website may be down
- Check: https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download
- Retry manually: Workflow → Re-run failed jobs

**Docker push fails**:
- Check Docker Hub credentials
- Ensure secrets are set: DOCKERHUB_USERNAME, DOCKERHUB_TOKEN
- Verify token has push permissions

**Database build produces 0 records**:
- FAA data format may have changed
- Check parsing logic in scripts/update_faa_data.py
- Review workflow logs for parsing errors

**Workflow not triggering on schedule**:
- GitHub may disable scheduled workflows after 60 days of inactivity
- Re-enable: Repository Settings → Actions → Enable workflows
- Trigger manually to reset timer

### Notifications

**Email notifications**:
- GitHub sends email on workflow failure (if enabled in settings)
- Configure: User Settings → Notifications → Actions

**Slack/Discord notifications** (future):
```yaml
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Security Considerations

### Secrets Management

**Required secrets**:
- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token (not password!)

**Optional secrets**:
- `PORTAINER_WEBHOOK_URL` - Portainer webhook for auto-deployment

**Best practices**:
1. Use Docker Hub tokens, not passwords
2. Rotate tokens periodically
3. Limit token permissions (push only)
4. Never commit secrets to code
5. Use repository secrets, not organization secrets (unless needed)

### Permissions

**Nightly build**:
- `contents: write` - For creating GitHub Releases
- `packages: write` - For publishing Docker images

**Code change build**:
- `contents: read` - For reading code
- `packages: write` - For publishing Docker images

**Why minimal permissions?**
- Principle of least privilege
- Reduce attack surface if workflow compromised
- Clear intent in workflow definition

### Dependency Security

**Renovate**:
- Configured in renovate.json
- Automatic dependency updates
- Can auto-merge patch updates

**Manual review**:
- Review dependency updates before merging
- Check for breaking changes
- Test locally before deploying

---

## Performance Optimization

### Build Time Optimization

**Current build times**:
- Nightly build: ~3-4 minutes
  - Database download: ~5 seconds
  - Database parsing: ~10 seconds
  - Database creation: ~15 seconds
  - Docker build: ~2 minutes (with cache)
  - Docker push: ~1 minute
- Code change build: ~2-3 minutes (reuses database)

**Optimization techniques**:
1. GitHub Actions cache for Docker layers
2. Reuse database from releases (code change workflow)
3. Batch database inserts (not individual INSERTs)
4. Only trigger on relevant file changes

**Future optimizations**:
- Multi-platform builds (requires buildx)
- Parallel database parsing
- Incremental database updates (if FAA provides)

### Image Size Optimization

**Current: ~225MB**

**Possible optimizations**:
1. Alpine base image (~50MB smaller, but complicates dependencies)
2. Multi-stage builds (not applicable, database must be in final image)
3. Compress database with zstd (decompression at runtime)
4. Remove unused Python packages

**Trade-offs**:
- Alpine: Smaller, but slower, compatibility issues
- Compression: Smaller download, slower startup
- Minimal dependencies: Already done (only FastAPI, Uvicorn, Pydantic)

---

## Deployment Integration

### Portainer Webhook

**Setup**:
1. In Portainer, navigate to service
2. Enable webhook
3. Copy webhook URL
4. Add to GitHub repository secrets as `PORTAINER_WEBHOOK_URL`

**How it works**:
1. Workflow completes successfully
2. Webhook step sends POST request to Portainer
3. Portainer pulls latest image
4. Portainer redeploys service automatically

**Benefits**:
- Zero-downtime deployments
- Automatic updates on nightly builds
- No manual intervention required

**Alternative: Watchtower**:
```yaml
watchtower:
  image: containrrr/watchtower
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  command: --interval 3600 tail-lookup
```

### Kubernetes (future)

For Kubernetes deployments:
1. Create Deployment manifest
2. Use `imagePullPolicy: Always` for latest tag
3. Set up image pull secrets for private registries
4. Use rolling update strategy

Example:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tail-lookup
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
  template:
    spec:
      containers:
      - name: tail-lookup
        image: ryakel/tail-lookup:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
```

---

## Testing in CI/CD

### Current State

No automated tests in workflows (application is straightforward).

### Future Testing

**Unit tests**:
```yaml
- name: Run unit tests
  run: |
    pip install pytest
    pytest tests/
```

**Integration tests**:
```yaml
- name: Test API endpoints
  run: |
    docker run -d -p 8080:8080 tail-lookup
    sleep 5
    curl -f http://localhost:8080/api/v1/health
    curl -f http://localhost:8080/api/v1/aircraft/N172SP
```

**Database tests**:
```yaml
- name: Verify database
  run: |
    RECORDS=$(sqlite3 data/aircraft.db "SELECT COUNT(*) FROM master")
    if [ "$RECORDS" -lt 200000 ]; then
      echo "Error: Too few records ($RECORDS)"
      exit 1
    fi
```

---

## Troubleshooting

### Workflow Fails on Schedule

**Symptom**: Nightly build doesn't run automatically

**Causes**:
1. Repository inactive for 60+ days (GitHub disables schedules)
2. Workflow file syntax error
3. GitHub Actions service issue

**Solutions**:
1. Trigger workflow manually to re-enable schedule
2. Validate YAML syntax: https://www.yamllint.com/
3. Check GitHub status: https://www.githubstatus.com/

### Docker Push Fails

**Symptom**: "unauthorized: authentication required"

**Causes**:
1. Docker Hub credentials not set
2. Token expired
3. Token lacks push permissions

**Solutions**:
1. Verify secrets are set in repository settings
2. Regenerate Docker Hub token
3. Ensure token has write permissions

### Database Build Produces Zero Records

**Symptom**: `record_count: 0` in health check

**Causes**:
1. FAA data format changed
2. Parsing logic broken
3. FAA website down during build

**Solutions**:
1. Check workflow logs for parsing errors
2. Manually download and inspect FAA files
3. Update parsing logic in scripts/update_faa_data.py
4. Trigger manual build retry

### Release Not Created

**Symptom**: GitHub Release missing after workflow

**Causes**:
1. `contents: write` permission missing
2. Release creation step failed
3. Tag already exists

**Solutions**:
1. Verify workflow permissions
2. Check step logs for errors
3. Delete existing tag if conflict

---

## Best Practices

1. **Use date tags for production**: Pin to specific date for stability
2. **Monitor nightly builds**: Check for failures weekly
3. **Rotate Docker Hub tokens**: Every 90 days
4. **Test workflow changes**: Use workflow_dispatch trigger for testing
5. **Keep database snapshots**: Don't delete old releases (helpful for debugging)
6. **Document secret requirements**: README should list required secrets
7. **Use branch protection**: Require PR reviews before merging to main

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Softprops Release Action](https://github.com/softprops/action-gh-release)
- [GitHub Actions Caching](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
