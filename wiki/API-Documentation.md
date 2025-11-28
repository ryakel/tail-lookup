# API Documentation

Comprehensive documentation for all tail-lookup API endpoints, request/response formats, and usage examples.

## Base URL

**Local Development**: `http://localhost:8080`
**Docker Container**: `http://localhost:8080` (or your mapped port)
**Production**: Depends on your deployment

## API Endpoints

### 1. Single Aircraft Lookup

Retrieve information for a single aircraft by tail number.

**Endpoint**: `GET /api/v1/aircraft/{tail}`

**Parameters**:
- `tail` (path, required): Aircraft tail number (N-number)
  - Formats accepted: `N172SP`, `172SP`, `N-172SP`, `n172sp`
  - Case-insensitive
  - 'N' prefix optional
  - Dashes and spaces stripped

**Response**: `200 OK` with `AircraftResponse` JSON
**Error**: `404 Not Found` if tail number not in database

**Success Response Schema**:
```json
{
  "tail_number": "string",
  "manufacturer": "string",
  "model": "string",
  "series": "string | null",
  "aircraft_type": "string",
  "engine_type": "string",
  "num_engines": "integer | null",
  "num_seats": "integer | null",
  "year_mfr": "integer | null"
}
```

**Example Request**:
```bash
curl http://localhost:8080/api/v1/aircraft/N172SP
```

**Example Success Response**:
```json
{
  "tail_number": "172SP",
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

**Example Error Response**:
```json
{
  "detail": "Aircraft not found"
}
```

**Notes**:
- Tail number is normalized before lookup (uppercase, strip N prefix and dashes)
- Optional fields (series, num_engines, num_seats, year_mfr) may be `null` if not in FAA data
- Aircraft type and engine type are human-readable strings (mapped from FAA numeric codes)

---

### 2. Bulk Aircraft Lookup

Retrieve information for multiple aircraft in a single request.

**Endpoint**: `POST /api/v1/aircraft/bulk`

**Request Body**: JSON with array of tail numbers (max 50)

**Request Schema**:
```json
{
  "tail_numbers": ["string", "string", ...]
}
```

**Response**: `200 OK` with `BulkResponse` JSON

**Response Schema**:
```json
{
  "total": "integer",
  "found": "integer",
  "results": [
    {
      "tail_number": "string",
      "manufacturer": "string | null",
      "model": "string | null",
      "series": "string | null",
      "aircraft_type": "string | null",
      "engine_type": "string | null",
      "num_engines": "integer | null",
      "num_seats": "integer | null",
      "year_mfr": "integer | null",
      "error": "string | null"
    }
  ]
}
```

**Example Request**:
```bash
curl -X POST http://localhost:8080/api/v1/aircraft/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "tail_numbers": ["N172SP", "N12345", "N99999"]
  }'
```

**Example Response**:
```json
{
  "total": 3,
  "found": 2,
  "results": [
    {
      "tail_number": "172SP",
      "manufacturer": "CESSNA",
      "model": "172S",
      "series": "SKYHAWK SP",
      "aircraft_type": "Fixed Wing Single-Engine",
      "engine_type": "Reciprocating",
      "num_engines": 1,
      "num_seats": 4,
      "year_mfr": 2001,
      "error": null
    },
    {
      "tail_number": "12345",
      "manufacturer": "BOEING",
      "model": "737-800",
      "series": null,
      "aircraft_type": "Fixed Wing Multi-Engine",
      "engine_type": "Turbo-Fan",
      "num_engines": 2,
      "num_seats": 189,
      "year_mfr": 2015,
      "error": null
    },
    {
      "tail_number": "99999",
      "manufacturer": null,
      "model": null,
      "series": null,
      "aircraft_type": null,
      "engine_type": null,
      "num_engines": null,
      "num_seats": null,
      "year_mfr": null,
      "error": "Not found"
    }
  ]
}
```

**Validation Rules**:
- Maximum 50 tail numbers per request
- Each tail number normalized same as single lookup
- Empty array returns `total: 0, found: 0, results: []`

**Error Handling**:
- Invalid tail numbers get `error: "Not found"` in results array
- Request doesn't fail if some tail numbers are invalid
- All requested tail numbers are returned in results (with or without error)

**Example Error Response (422 Validation Error)**:
```json
{
  "detail": [
    {
      "type": "too_many_items",
      "loc": ["body", "tail_numbers"],
      "msg": "List should have at most 50 items after validation, not 51",
      "input": [...],
      "ctx": {"field_type": "List", "max_length": 50}
    }
  ]
}
```

**Notes**:
- Use bulk endpoint for batch processing, not single lookups
- Results are returned in same order as input
- Performance: ~5ms for 50 lookups (0.1ms per aircraft)

---

### 3. Health Check

Check API and database health status.

**Endpoint**: `GET /api/v1/health`

**Response**: `200 OK` with `HealthResponse` JSON

**Response Schema**:
```json
{
  "status": "string",
  "database_exists": "boolean",
  "record_count": "integer",
  "last_updated": "string | null"
}
```

**Example Request**:
```bash
curl http://localhost:8080/api/v1/health
```

**Example Response**:
```json
{
  "status": "healthy",
  "database_exists": true,
  "record_count": 297431,
  "last_updated": "2025-11-28T06:15:23Z"
}
```

**Status Values**:
- `"healthy"`: Database exists and has records
- `"unhealthy"`: Database doesn't exist or has 0 records

**Notes**:
- Used by Docker health check
- `last_updated` shows when database was last built
- `record_count` varies slightly as FAA registrations change (~297K-305K typical)

---

### 4. Database Statistics

Get database statistics and information.

**Endpoint**: `GET /api/v1/stats`

**Response**: `200 OK` with `StatsResponse` JSON

**Response Schema**:
```json
{
  "record_count": "integer",
  "last_updated": "string | null"
}
```

**Example Request**:
```bash
curl http://localhost:8080/api/v1/stats
```

**Example Response**:
```json
{
  "record_count": 297431,
  "last_updated": "2025-11-28T06:15:23Z"
}
```

**Notes**:
- Similar to health check but without status field
- Used by web UI to display database info

---

### 5. Web UI

Interactive browser-based interface for testing the API.

**Endpoint**: `GET /`

**Response**: HTML page (web interface)

**Features**:
- Single aircraft lookup with real-time validation
- Bulk lookup (paste multiple tail numbers, one per line)
- Database statistics display
- Dark theme
- Responsive design

**Example**:
Open `http://localhost:8080` in your browser.

---

### 6. OpenAPI Documentation

Interactive API documentation with request/response examples.

**Endpoint**: `GET /docs`

**Response**: Swagger UI HTML page

**Features**:
- Interactive API explorer
- Try-it-out functionality
- Request/response schemas
- Auto-generated from Pydantic models

**Example**:
Open `http://localhost:8080/docs` in your browser.

---

### 7. Alternative API Documentation

Alternative API documentation interface.

**Endpoint**: `GET /redoc`

**Response**: ReDoc HTML page

**Features**:
- Clean, readable documentation
- Three-panel layout
- Request/response examples
- Auto-generated from Pydantic models

**Example**:
Open `http://localhost:8080/redoc` in your browser.

---

### 8. OpenAPI JSON Schema

Raw OpenAPI specification in JSON format.

**Endpoint**: `GET /openapi.json`

**Response**: JSON schema

**Use Cases**:
- Generate client libraries (e.g., with openapi-generator)
- Import into API tools (e.g., Postman, Insomnia)
- Integration with API gateways

**Example**:
```bash
curl http://localhost:8080/openapi.json > openapi.json
```

---

## Request/Response Details

### Content Types

**Requests**:
- Single lookup: N/A (path parameter)
- Bulk lookup: `application/json`

**Responses**:
- JSON endpoints: `application/json`
- Web UI: `text/html`
- OpenAPI: `application/json` or `text/html`

### Character Encoding

All endpoints use UTF-8 encoding.

### CORS

CORS is enabled for all origins:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, OPTIONS`
- `Access-Control-Allow-Headers: *`

This allows web applications from any domain to call the API.

### Rate Limiting

Currently no rate limiting implemented. Consider adding for production:
- Per-IP rate limiting
- API key-based quotas
- Bulk endpoint specific limits

### Error Responses

All errors follow FastAPI's standard error format:

**404 Not Found**:
```json
{
  "detail": "Aircraft not found"
}
```

**422 Validation Error**:
```json
{
  "detail": [
    {
      "type": "error_type",
      "loc": ["location", "field"],
      "msg": "Error message",
      "input": "user_input"
    }
  ]
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Internal server error"
}
```

---

## Usage Examples

### Python with requests

```python
import requests

# Single lookup
response = requests.get("http://localhost:8080/api/v1/aircraft/N172SP")
if response.status_code == 200:
    aircraft = response.json()
    print(f"{aircraft['tail_number']}: {aircraft['manufacturer']} {aircraft['model']}")
else:
    print("Not found")

# Bulk lookup
response = requests.post(
    "http://localhost:8080/api/v1/aircraft/bulk",
    json={"tail_numbers": ["N172SP", "N12345", "N99999"]}
)
data = response.json()
print(f"Found {data['found']} of {data['total']} aircraft")
for result in data['results']:
    if result['error']:
        print(f"{result['tail_number']}: {result['error']}")
    else:
        print(f"{result['tail_number']}: {result['manufacturer']} {result['model']}")
```

### JavaScript with fetch

```javascript
// Single lookup
fetch('http://localhost:8080/api/v1/aircraft/N172SP')
  .then(response => response.json())
  .then(data => {
    console.log(`${data.tail_number}: ${data.manufacturer} ${data.model}`);
  })
  .catch(error => console.error('Not found'));

// Bulk lookup
fetch('http://localhost:8080/api/v1/aircraft/bulk', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tail_numbers: ['N172SP', 'N12345', 'N99999']
  })
})
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.found} of ${data.total} aircraft`);
    data.results.forEach(result => {
      if (result.error) {
        console.log(`${result.tail_number}: ${result.error}`);
      } else {
        console.log(`${result.tail_number}: ${result.manufacturer} ${result.model}`);
      }
    });
  });
```

### curl Examples

```bash
# Single lookup (basic)
curl http://localhost:8080/api/v1/aircraft/N172SP

# Single lookup (pretty print with jq)
curl http://localhost:8080/api/v1/aircraft/N172SP | jq

# Bulk lookup
curl -X POST http://localhost:8080/api/v1/aircraft/bulk \
  -H "Content-Type: application/json" \
  -d '{"tail_numbers": ["N172SP", "N12345"]}'

# Health check
curl http://localhost:8080/api/v1/health

# Stats
curl http://localhost:8080/api/v1/stats

# Download OpenAPI spec
curl http://localhost:8080/openapi.json > openapi.json
```

### Shell Script Example

```bash
#!/bin/bash

# Lookup multiple tail numbers from file (one per line)
while IFS= read -r tail; do
    echo -n "$tail: "
    curl -s "http://localhost:8080/api/v1/aircraft/$tail" | \
        jq -r 'if .detail then "Not found" else "\(.manufacturer) \(.model)" end'
done < tail_numbers.txt
```

### Excel Integration (VBA)

```vba
Function LookupAircraft(tailNumber As String) As String
    Dim http As Object
    Dim url As String
    Dim response As String

    Set http = CreateObject("MSXML2.XMLHTTP")
    url = "http://localhost:8080/api/v1/aircraft/" & tailNumber

    http.Open "GET", url, False
    http.Send

    If http.Status = 200 Then
        ' Parse JSON response (simplified)
        LookupAircraft = http.responseText
    Else
        LookupAircraft = "Not found"
    End If
End Function
```

---

## Data Format Details

### Tail Number Normalization

The API normalizes all tail numbers before lookup:

1. Convert to uppercase
2. Strip leading 'N' if present
3. Remove dashes and spaces
4. Trim whitespace

**Examples**:
- `N172SP` → `172SP`
- `n172sp` → `172SP`
- `N-172SP` → `172SP`
- `172SP` → `172SP`
- `N 172 SP` → `172SP`

### Aircraft Types

Human-readable strings mapped from FAA numeric codes:
- "Glider"
- "Balloon"
- "Blimp/Dirigible"
- "Fixed Wing Single-Engine"
- "Fixed Wing Multi-Engine"
- "Rotorcraft"
- "Weight-Shift-Control"
- "Powered Parachute"
- "Gyroplane"
- "Hybrid Lift"
- "Other"

### Engine Types

Human-readable strings mapped from FAA numeric codes:
- "None"
- "Reciprocating" (piston)
- "Turbo-Prop"
- "Turbo-Shaft"
- "Turbo-Jet"
- "Turbo-Fan"
- "Ramjet"
- "2 Cycle"
- "4 Cycle"
- "Unknown"
- "Electric"
- "Rotary"

### Optional Fields

These fields may be `null` if not in FAA database:
- `series`: Aircraft series/variant name
- `num_engines`: Number of engines
- `num_seats`: Number of seats
- `year_mfr`: Year of manufacture
- `last_updated`: Database update timestamp (if never built)

---

## Client Libraries

### Generate Client

Use OpenAPI Generator to create client libraries:

```bash
# Download OpenAPI spec
curl http://localhost:8080/openapi.json > openapi.json

# Generate Python client
openapi-generator-cli generate \
  -i openapi.json \
  -g python \
  -o ./client-python

# Generate TypeScript client
openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-fetch \
  -o ./client-typescript

# Generate Go client
openapi-generator-cli generate \
  -i openapi.json \
  -g go \
  -o ./client-go
```

### Community Clients

Feel free to create and share client libraries for your language of choice. The OpenAPI spec makes it easy to generate type-safe clients.

---

## Performance

### Latency

**Single Lookup**: ~1-2ms (local), ~10-50ms (network)
**Bulk Lookup (50 aircraft)**: ~5-10ms (local), ~20-100ms (network)
**Health Check**: <1ms
**Stats**: <1ms

### Throughput

**Single requests**: ~1000 req/sec on modest hardware
**Bulk requests**: ~100 req/sec (50 aircraft each = 5000 lookups/sec)

### Optimization Tips

1. **Use bulk endpoint** for multiple lookups (one request vs many)
2. **Cache responses** client-side (data changes once daily)
3. **Parallel requests** if needed (API is async, handles concurrent well)
4. **Connection pooling** for high-volume usage

---

## Best Practices

1. **Normalize tail numbers** client-side before sending (optional, API does it anyway)
2. **Handle null fields** gracefully (not all aircraft have complete data)
3. **Check error field** in bulk responses (some lookups may fail)
4. **Cache aggressively** (data only updates once daily)
5. **Use bulk endpoint** for batch processing (more efficient)
6. **Monitor health endpoint** to detect stale data or outages
7. **Handle 404** gracefully (not all N-numbers are registered)

---

## Troubleshooting

**404 Not Found for valid tail number**:
- Verify tail number is correct (check FAA registry)
- Aircraft may be deregistered or not yet registered
- Database may be stale (check health endpoint)

**422 Validation Error**:
- Check request format matches schema
- Ensure max 50 tail numbers for bulk
- Verify Content-Type header is application/json

**Connection Refused**:
- Verify API is running (`docker ps` or check process)
- Check port mapping (default 8080)
- Verify firewall allows connections

**Slow responses**:
- Check database size (should be ~25MB)
- Verify SQLite index exists
- Monitor system resources

**Stale data**:
- Check last_updated in health endpoint
- Verify nightly build workflow is running
- Trigger manual workflow run if needed

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Models](https://docs.pydantic.dev/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [FAA Aircraft Registry](https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry)
