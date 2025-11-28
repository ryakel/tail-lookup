# Database Design

This document details the SQLite database schema, data sources, and design decisions for the tail-lookup database.

## Overview

The tail-lookup database is a SQLite database containing FAA aircraft registration data. It consists of three tables and is optimized for read-heavy lookup operations.

**Database Size**: ~25MB
**Record Count**: ~300,000 aircraft registrations
**Update Frequency**: Daily at 6 AM UTC
**Source**: FAA Releasable Aircraft Database

## Schema Design

### master Table

The `master` table contains aircraft registration records from the FAA MASTER.txt file.

```sql
CREATE TABLE master (
    n_number TEXT PRIMARY KEY,           -- Aircraft N-number (without 'N' prefix)
    serial_number TEXT,                  -- Manufacturer serial number
    mfr_mdl_code TEXT,                  -- Manufacturer model code (FK to acftref)
    eng_mfr_mdl TEXT,                   -- Engine manufacturer/model
    year_mfr INTEGER,                   -- Year of manufacture
    type_registrant TEXT,               -- Type of registrant (1-9 code)
    name TEXT,                          -- Registrant name
    street TEXT,                        -- Registrant street address
    street2 TEXT,                       -- Registrant street address line 2
    city TEXT,                          -- Registrant city
    state TEXT,                         -- Registrant state
    zip_code TEXT,                      -- Registrant ZIP code
    region TEXT,                        -- FAA region code
    county TEXT,                        -- County code
    country TEXT,                       -- Country code
    last_action_date TEXT,              -- Last action date (YYYYMMDD)
    cert_issue_date TEXT,               -- Certificate issue date (YYYYMMDD)
    certification TEXT,                 -- Aircraft certification (1-10 code)
    type_aircraft TEXT,                 -- Aircraft type code (1-9)
    type_engine TEXT,                   -- Engine type code (0-11)
    status_code TEXT,                   -- Registration status
    mode_s_code TEXT,                   -- Mode S transponder code
    fract_owner TEXT,                   -- Fractional ownership (Y/N)
    air_worth_date TEXT,                -- Airworthiness date (YYYYMMDD)
    other_names_1 TEXT,                 -- Other registered names
    other_names_2 TEXT,
    other_names_3 TEXT,
    other_names_4 TEXT,
    other_names_5 TEXT,
    expiration_date TEXT,               -- Registration expiration (YYYYMMDD)
    unique_id TEXT,                     -- Unique identifier
    kit_mfr TEXT,                       -- Kit manufacturer (if homebuilt)
    kit_model TEXT,                     -- Kit model (if homebuilt)
    mode_s_code_hex TEXT                -- Mode S code in hexadecimal
);

-- Index for JOIN optimization with acftref table
CREATE INDEX idx_mfr_mdl_code ON master(mfr_mdl_code);
```

**Key Fields**:
- `n_number`: Primary key, normalized without 'N' prefix (e.g., "172SP")
- `mfr_mdl_code`: Foreign key to acftref table for aircraft details
- `year_mfr`: Integer for easy filtering/sorting
- `type_aircraft`, `type_engine`: Numeric codes mapped to human-readable names in Python

**Design Decisions**:
- **Why TEXT for n_number?** N-numbers can contain letters and numbers, not purely numeric
- **Why store without 'N' prefix?** Normalization for consistent lookups
- **Why TEXT for dates?** FAA format is YYYYMMDD, stored as-is for simplicity
- **Why separate address fields?** Maintain FAA data structure, allow flexible queries
- **Why index on mfr_mdl_code?** This is the JOIN key, critical for performance

### acftref Table

The `acftref` table contains aircraft model reference data from the FAA ACFTREF.txt file.

```sql
CREATE TABLE acftref (
    code TEXT PRIMARY KEY,              -- Manufacturer model code
    mfr TEXT,                           -- Manufacturer name
    model TEXT,                         -- Model designation
    type_acft TEXT,                     -- Aircraft type code (1-9)
    type_eng TEXT,                      -- Engine type code (0-11)
    ac_cat TEXT,                        -- Aircraft category
    build_cert_ind TEXT,                -- Builder certification indicator
    no_eng INTEGER,                     -- Number of engines
    no_seats INTEGER,                   -- Number of seats
    ac_weight TEXT,                     -- Aircraft weight class
    speed TEXT                          -- Speed class
);
```

**Key Fields**:
- `code`: Primary key, links to master.mfr_mdl_code
- `mfr`: Manufacturer name (e.g., "CESSNA", "BOEING")
- `model`: Model designation (e.g., "172S", "737-800")
- `type_acft`, `type_eng`: Numeric codes for type classification
- `no_eng`, `no_seats`: Integer values for specifications

**Design Decisions**:
- **Why separate table?** Normalize model data, avoid duplication
- **Why INTEGER for counts?** Enable numeric comparisons and aggregations
- **Why TEXT for weight/speed?** FAA uses class codes (e.g., "CLASS 1"), not numeric values

### metadata Table

The `metadata` table stores database metadata and update tracking.

```sql
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,               -- Metadata key
    value TEXT                          -- Metadata value
);
```

**Current Metadata**:
- `last_updated`: ISO 8601 timestamp of when database was built

**Design Decisions**:
- **Why key-value structure?** Flexible for adding new metadata without schema changes
- **Why store last_updated?** Used by health check endpoint to show data freshness
- **Future use cases**: Could store FAA data version, build hash, etc.

## Data Source: FAA Releasable Aircraft Database

### Source Information

**Official URL**: https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download

**File**: ReleasableAircraft.zip (~30MB compressed)

**Update Schedule**: FAA updates daily at 11:30 PM CT (5:30 AM UTC)

**Our Update Schedule**: Daily at 6:00 AM UTC (30-minute buffer)

### File Formats

#### MASTER.txt

**Format**: Fixed-width text file
**Records**: ~300,000 active registrations
**Encoding**: ASCII

**Column Positions** (from FAA documentation):
```
N-NUMBER          1-5
SERIAL_NUMBER     6-35
MFR_MDL_CODE      36-42
ENG_MFR_MDL       43-47
YEAR_MFR          48-51
TYPE_REGISTRANT   52
NAME              53-102
STREET            103-135
STREET2           136-168
CITY              169-186
STATE             187-188
ZIP_CODE          189-197
REGION            198-199
COUNTY            200-202
COUNTRY           203-204
LAST_ACTION_DATE  205-212
CERT_ISSUE_DATE   213-220
CERTIFICATION     221-228
TYPE_AIRCRAFT     229
TYPE_ENGINE       230
STATUS_CODE       231-240
MODE_S_CODE       241-248
FRACT_OWNER       249
AIR_WORTH_DATE    250-257
OTHER_NAMES_1     258-307
OTHER_NAMES_2     308-357
OTHER_NAMES_3     358-407
OTHER_NAMES_4     408-457
OTHER_NAMES_5     458-507
EXPIRATION_DATE   508-515
UNIQUE_ID         516-522
KIT_MFR           523-552
KIT_MODEL         553-572
MODE_S_CODE_HEX   573-582
```

**Parsing Strategy**:
1. Read file line by line
2. Extract each field using slice indices (positions - 1 for 0-based)
3. Strip whitespace from extracted strings
4. Convert year to integer if present
5. Skip header row
6. Insert in batch for performance

#### ACFTREF.txt

**Format**: Fixed-width text file
**Records**: ~10,000 aircraft models
**Encoding**: ASCII

**Column Positions** (from FAA documentation):
```
CODE              1-7
MFR               8-37
MODEL             38-57
TYPE_ACFT         58
TYPE_ENG          59-60
AC_CAT            61
BUILD_CERT_IND    62
NO_ENG            63
NO_SEATS          64-66
AC_WEIGHT         67-73
SPEED             74-77
```

**Parsing Strategy**:
1. Read file line by line
2. Extract each field using slice indices
3. Strip whitespace
4. Convert no_eng and no_seats to integers if present
5. Skip header row
6. Insert in batch for performance

### Data Quality Considerations

**Missing Data**:
- Not all aircraft have year_mfr, serial_number, etc.
- Some fields are blank in FAA data
- Our API returns `null` for missing optional fields

**Data Inconsistencies**:
- Manufacturer names have varying formats (e.g., "CESSNA" vs "CESSNA AIRCRAFT CO")
- Some model codes in master don't exist in acftref (rare)
- Date formats are YYYYMMDD strings, not ISO 8601

**Handling Strategy**:
- Optional fields in Pydantic models allow null
- LEFT JOIN ensures we return data even if acftref lookup fails
- Input validation prevents malformed requests

## Type Code Mappings

The FAA uses numeric codes for aircraft and engine types. We map these to human-readable strings in `database.py`.

### Aircraft Type Codes

```python
AIRCRAFT_TYPES = {
    "1": "Glider",
    "2": "Balloon",
    "3": "Blimp/Dirigible",
    "4": "Fixed Wing Single-Engine",
    "5": "Fixed Wing Multi-Engine",
    "6": "Rotorcraft",
    "7": "Weight-Shift-Control",
    "8": "Powered Parachute",
    "9": "Gyroplane",
    "H": "Hybrid Lift",
    "O": "Other"
}
```

**Source**: FAA aircraft type classification

**Most Common**:
- Type 4: Fixed Wing Single-Engine (~60% of registrations)
- Type 5: Fixed Wing Multi-Engine (~25% of registrations)
- Type 6: Rotorcraft (~10% of registrations)

### Engine Type Codes

```python
ENGINE_TYPES = {
    "0": "None",
    "1": "Reciprocating",
    "2": "Turbo-Prop",
    "3": "Turbo-Shaft",
    "4": "Turbo-Jet",
    "5": "Turbo-Fan",
    "6": "Ramjet",
    "7": "2 Cycle",
    "8": "4 Cycle",
    "9": "Unknown",
    "10": "Electric",
    "11": "Rotary"
}
```

**Source**: FAA engine type classification

**Most Common**:
- Type 1: Reciprocating (~65% of registrations) - piston engines
- Type 2: Turbo-Prop (~20% of registrations)
- Type 5: Turbo-Fan (~10% of registrations) - jets

## Query Patterns

### Single Aircraft Lookup

```sql
SELECT
    m.n_number,
    m.year_mfr,
    m.type_aircraft,
    m.type_engine,
    a.mfr,
    a.model,
    a.model as series,
    a.no_eng,
    a.no_seats
FROM master m
LEFT JOIN acftref a ON m.mfr_mdl_code = a.code
WHERE m.n_number = ?
```

**Explanation**:
- LEFT JOIN ensures we get master record even if acftref match fails
- Parameterized query prevents SQL injection
- Index on m.mfr_mdl_code makes JOIN fast
- Primary key lookup on n_number is O(log n) with B-tree index

**Performance**: ~0.1ms per query on typical hardware

### Bulk Aircraft Lookup

Same query executed N times in Python loop (where N ≤ 50).

**Why not single query?**
- Variable-length IN clause is harder to optimize
- Individual lookups allow per-tail error handling
- Performance is still excellent (~5ms for 50 lookups)

**Future optimization**: Could use single query with IN clause for better performance at scale.

### Health Check Query

```sql
SELECT COUNT(*) FROM master
```

**Purpose**: Verify database is accessible and has records

**Performance**: Fast count on small database, no index needed

### Statistics Query

```sql
SELECT value FROM metadata WHERE key = 'last_updated'
```

**Purpose**: Show when database was last updated

**Performance**: Single-row primary key lookup, instant

## Database Build Process

See `scripts/update_faa_data.py` for implementation details.

### Build Steps

1. **Download**
   - Fetch ReleasableAircraft.zip from FAA (~30MB)
   - Verify download completed successfully
   - Extract zip to temporary directory

2. **Parse MASTER.txt**
   - Read file line by line (avoid loading entire file in memory)
   - Skip header row
   - Extract fields using fixed-width positions
   - Normalize n_number (strip 'N' prefix, uppercase)
   - Convert year_mfr to integer if present
   - Collect all records in list

3. **Parse ACFTREF.txt**
   - Read file line by line
   - Skip header row
   - Extract fields using fixed-width positions
   - Convert no_eng and no_seats to integers if present
   - Collect all records in list

4. **Create Database**
   - Create SQLite database file
   - Execute CREATE TABLE statements
   - Execute CREATE INDEX statement
   - Insert all master records in single batch transaction
   - Insert all acftref records in single batch transaction
   - Insert metadata record with current timestamp
   - Commit transaction
   - Close database

5. **Cleanup**
   - Remove temporary files
   - Remove downloaded zip

### Build Time

**Local Build**: ~30 seconds on modern hardware
- Download: ~5 seconds (depends on internet speed)
- Parsing: ~10 seconds
- Database creation: ~10 seconds
- Indexing: ~5 seconds

**CI/CD Build**: ~45 seconds on GitHub Actions runners

### Build Optimizations

**Why batch insert?**
- Individual INSERT statements: ~5 minutes for 300K records
- Batch INSERT with transaction: ~10 seconds
- 30x speedup!

**Why index after insert?**
- Inserting into indexed table is slower
- Creating index after bulk insert is faster
- Overall build time is reduced

**Memory usage**:
- Streaming file read: ~100MB peak (reading line by line)
- Batch insert: ~200MB peak (holding records in memory)
- Total: ~300MB peak during build
- Final database: ~25MB on disk

## Database Maintenance

### Updates

**Automated**: GitHub Actions nightly build workflow runs daily at 6 AM UTC

**Manual**: Run `python scripts/update_faa_data.py data/aircraft.db`

### Backup

**Automated**: GitHub Releases stores database snapshot with each build

**Download**: `curl -L -o aircraft.db https://github.com/ryakel/tail-lookup/releases/latest/download/aircraft.db`

### Verification

**Check record count**:
```bash
sqlite3 data/aircraft.db "SELECT COUNT(*) FROM master"
```

**Check last updated**:
```bash
sqlite3 data/aircraft.db "SELECT value FROM metadata WHERE key='last_updated'"
```

**Check database size**:
```bash
du -h data/aircraft.db
```

Expected values:
- Record count: ~300,000 (±10,000 as registrations change)
- Size: ~25MB (±2MB)
- Last updated: Recent date (within 24 hours if automated builds are working)

### Troubleshooting

**Database file not found**:
- Ensure `data/` directory exists
- Run build script manually
- Check GitHub Releases for pre-built database

**Record count is zero**:
- FAA download may have failed
- Check FAA website is accessible
- Verify parsing logic hasn't broken due to FAA format change

**Database is much larger than expected**:
- May have duplicate records (check parsing logic)
- May have included test data or other files

**Old last_updated timestamp**:
- Nightly build workflow may not be running
- Check GitHub Actions logs
- Trigger manual workflow run

## Future Enhancements

### Potential Schema Changes

1. **Full-text search**
   - Add FTS5 virtual table for manufacturer/model search
   - Enable queries like "find all Cessna 172 variants"

2. **Historical tracking**
   - Add history table with timestamp + record snapshot
   - Track registrations over time
   - Show when aircraft changed hands

3. **Computed columns**
   - Add age column (current_year - year_mfr)
   - Add display_name (with 'N' prefix)

4. **Additional indexes**
   - Index on manufacturer for search
   - Index on year_mfr for filtering
   - Index on state for geographic queries

### Migration to PostgreSQL

**When to consider**:
- Need for concurrent writes
- Need for complex queries with aggregations
- Multi-container deployment with shared database
- Horizontal scaling requirements

**Migration strategy**:
1. Create equivalent PostgreSQL schema
2. Add connection pooling (e.g., pgbouncer)
3. Update database.py to support both SQLite and PostgreSQL
4. Add environment variable to choose backend
5. Update CI/CD to build both options

**Trade-offs**:
- PostgreSQL: Better concurrency, more features, requires external database
- SQLite: Simpler deployment, lower latency, sufficient for read-only workload

**Current recommendation**: Stick with SQLite unless specific need arises.

## References

- [FAA Aircraft Registry](https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry)
- [FAA Releasable Database](https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [SQLite Performance Tuning](https://www.sqlite.org/performance.html)
