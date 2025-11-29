# Release Process

This document describes the automated release process for tail-lookup.

## Overview

Releases are automatically created when code is merged from `develop` to `main`. The process is fully automated and includes:

- Semantic versioning (MAJOR.MINOR.PATCH)
- Automatic version bump detection
- GitHub release creation with release notes
- Docker image tagging with version number
- Database artifact upload (aircraft.db)
- Database statistics in release notes

## Branching Strategy

```
develop (active development)
    ↓
    PR → main (production releases)
    ↓
    Automatic release created with database
```

## Version Bump Detection

The release workflow automatically determines the version bump type based on commit messages:

### Major Version (x.0.0)
Triggered by commit messages containing:
- `breaking:`
- `major:`

**Example**: `breaking: Change API endpoint structure`

### Minor Version (0.x.0)
Triggered by commit messages containing:
- `feat:`
- `feature:`
- `minor:`

**Example**: `feat: Add caching layer for frequent lookups`

### Patch Version (0.0.x)
All other commits (bug fixes, documentation, etc.)

**Example**: `fix: Correct NO-ENG and NO-SEATS parsing`

## Release Workflow

### 1. Develop Branch Work

```bash
# Work on develop branch
git checkout develop
git pull origin develop

# Make changes
git add .
git commit -m "feat: Add new API endpoint"
git push origin develop
```

### 2. Create Pull Request

```bash
# Create PR from develop to main
gh pr create --base main --head develop \
  --title "Release: [Brief description]" \
  --body "$(cat <<'EOF'
## Summary
[Describe changes]

## Changes
- Feature 1
- Feature 2
- Bug fix 1

## Database Changes
- Updated FAA data parsing
- Added new fields: [list]

## Testing
- [ ] Local testing complete
- [ ] Docker build successful
- [ ] API tests passed
- [ ] Database integrity verified

## Docker Images
- ryakel/tail-lookup:latest
EOF
)"
```

### 3. Merge Pull Request

When the PR is merged to `main`:

1. **Docker Build Workflow** (`build-main.yml`) runs:
   - Builds database from FAA data or downloads from latest release
   - Builds multi-architecture images (amd64, arm64) in parallel
   - Pushes to Docker Hub with digest
   - Creates multi-platform manifest
   - Tags with `latest` and date stamp

2. **Release Workflow** (`release.yml`) runs:
   - Analyzes commits since last release
   - Determines version bump (major/minor/patch)
   - Builds fresh database for statistics
   - Creates Git tag (e.g., `v1.2.3`)
   - Extracts recent changes from `.claude/session-notes.md`
   - Creates GitHub Release with:
     - Release notes
     - Database statistics (record count, update date)
     - Database artifact (aircraft.db)
     - Docker pull commands
     - Integration instructions

### 4. Automatic Release Creation

The release includes:

- **Version tag** (e.g., `v1.2.3`)
- **Release notes** with:
  - Database information (records, last updated)
  - Quick start instructions
  - Integration guide for flight-budget
  - Recent changes
  - Docker pull commands
  - Full commit list
- **Docker images** automatically tagged:
  - `ryakel/tail-lookup:latest`
  - `ryakel/tail-lookup:YYYY-MM-DD`
- **Database artifact** (`aircraft.db`) attached to release

## Database in Releases

Each release includes the FAA database as a downloadable artifact:

```bash
# Download database from latest release
curl -L -o aircraft.db \
  https://github.com/ryakel/tail-lookup/releases/latest/download/aircraft.db

# Or use in your own application
wget https://github.com/ryakel/tail-lookup/releases/latest/download/aircraft.db
```

The database is automatically:
- Built from latest FAA data
- Statistics calculated (record count)
- Uploaded as release asset
- Used by subsequent builds (downloaded instead of rebuilt)

## Commit Message Convention

Use semantic commit messages for proper version bumping:

```bash
# Major version bump (breaking changes)
git commit -m "breaking: Change API response structure"

# Minor version bump (new features)
git commit -m "feat: Add aircraft manufacturer search endpoint"
git commit -m "feature: Implement caching layer"

# Patch version bump (bug fixes, docs, etc)
git commit -m "fix: Correct NO-ENG parsing from MASTER.txt"
git commit -m "docs: Update API documentation"
git commit -m "chore: Update dependencies"
```

## Maintaining Session Notes

Keep `.claude/session-notes.md` up to date with all changes. The release workflow extracts recent content from this file for release notes.

### Session Notes Format

```markdown
# tail-lookup Session Notes

## Feature Name (Session YYYY-MM-DD)

**Goal**: Brief description

**Changes Made**:
1. Change 1
2. Change 2

**Benefits**:
- Benefit 1
- Benefit 2

**Testing Results**:
- Test 1: ✅
- Test 2: ✅

## Bug Fix Name (Session YYYY-MM-DD)

**Problem**: Description of issue

**Root Cause**: Why it happened

**Fix**: How it was resolved

**Result**: Outcome after fix
```

## Docker Hub Integration

After a release is created, Docker images are automatically available:

```bash
# Pull specific date version
docker pull ryakel/tail-lookup:2025-11-28

# Pull latest
docker pull ryakel/tail-lookup:latest

# Run the service
docker run -d -p 8080:8080 ryakel/tail-lookup:latest

# Test the API
curl http://localhost:8080/api/v1/aircraft/N172SP
```

## Integration with flight-budget

After tail-lookup releases, update flight-budget deployment:

```yaml
# docker-compose.yml
services:
  tail-lookup:
    image: ryakel/tail-lookup:latest  # or specific version
    # ... rest of config
```

The flight-budget `build-main.yml` workflow automatically downloads the latest database from tail-lookup releases.

## Nightly Builds

In addition to releases, nightly builds run automatically:

- **Schedule**: Every night at 2 AM UTC
- **Purpose**: Keep FAA data fresh
- **Process**:
  - Build fresh database from FAA data
  - Build multi-arch images in parallel
  - Push to Docker Hub with date tag
  - No GitHub release created

```bash
# Pull nightly build
docker pull ryakel/tail-lookup:2025-11-28
```

## Manual Release (Emergency)

If you need to create a manual release:

```bash
# Create and push tag
git checkout main
git pull origin main
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3

# Build database manually
python scripts/update_faa_data.py data/aircraft.db

# Create release via GitHub CLI with database
gh release create v1.2.3 \
  --title "Release v1.2.3" \
  --notes "Emergency release notes here" \
  data/aircraft.db
```

## Troubleshooting

### Release workflow didn't trigger

**Check**:
- Workflow file exists: `.github/workflows/release.yml`
- Push was to `main` branch
- Changes weren't only to ignored paths (`.github/**`, `wiki/**`, `*.md`)

### Wrong version number generated

**Fix**:
- Delete the incorrect tag: `git push --delete origin v1.2.3`
- Update commit messages to follow convention
- Merge again

### Database statistics incorrect

**Check**:
- FAA data download successful
- Database build completed without errors
- Record count query executed successfully

### Release notes are incomplete

**Fix**:
- Update `.claude/session-notes.md` with missing information
- Create a new patch release with documentation updates

### Docker images not tagged correctly

**Check**:
- `build-main.yml` workflow completed successfully
- Docker Hub credentials are configured
- Multi-platform manifest created successfully

### Database artifact missing

**Check**:
- Database built successfully in release workflow
- File exists at `data/aircraft.db`
- Upload step completed without errors

## Database Versioning

Each release contains:
- Docker image with embedded database
- Separate database artifact for download
- Statistics (record count, date) in release notes

To use a specific database version:

```bash
# Download from specific release
curl -L -o aircraft.db \
  https://github.com/ryakel/tail-lookup/releases/download/v1.2.3/aircraft.db

# Or use specific Docker image
docker pull ryakel/tail-lookup:2025-11-28
```

## Best Practices

1. **Keep session notes updated** - Document changes as you develop
2. **Use semantic commits** - Follow commit message conventions
3. **Test database changes** - Verify FAA data parsing works correctly
4. **Test before merging** - Ensure all API tests pass on develop
5. **Review Docker builds** - Verify multi-arch images build successfully
6. **Monitor releases** - Check GitHub releases and database stats
7. **Coordinate with flight-budget** - Ensure compatibility maintained

## Related Documentation

- [CI/CD Pipeline](CI-CD-Pipeline.md) - Build and deployment workflows
- [Database Schema](Database-Schema.md) - FAA database structure
- [API Documentation](API-Documentation.md) - REST API endpoints
- [Integration Guide](https://github.com/ryakel/flight-budget/blob/main/infrastructure/examples/README.md) - flight-budget integration

## Questions?

- 🐛 [Open an Issue](https://github.com/ryakel/tail-lookup/issues)
- 💬 [Start a Discussion](https://github.com/ryakel/tail-lookup/discussions)
