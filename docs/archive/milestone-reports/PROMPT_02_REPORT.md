# PHASE 2 REPORT — BACKEND FOUNDATION & API ARCHITECTURE
**Project:** Motorsport Incident Intelligence (MII)  
**Phase:** 02 — Backend Foundation & Relational Schema Layer  
**Document:** `docs/progress/PROMPT_02_REPORT.md`  
**Date:** September 2026  
**Status:** Completed & Validated (24/24 Tests Passing, Zero Frontend Disruption)

---

## 1. Backend Architecture Created

A modular, production-ready FastAPI backend architecture was implemented under `backend/app/`, maintaining strict separation of concerns across core configuration, relational database persistence, Pydantic validation, and REST API routing:

```
backend/
├── app/
│   ├── __init__.py                  # Package root (version 1.0.0)
│   ├── main.py                      # FastAPI application factory, lifespan, CORS & router aggregation
│   ├── api/                         # API route controllers
│   │   ├── __init__.py              # Aggregates all v1 feature routers
│   │   ├── health.py                # System diagnostics & cache readiness
│   │   ├── races.py                 # Championship events & calendar queries
│   │   ├── sessions.py              # Session metadata, activity histogram & dashboard summaries
│   │   ├── drivers.py               # Driver transponder rosters & profiles
│   │   ├── incidents.py             # Incident candidates & steward review status updates
│   │   ├── telemetry.py             # Bounded timeseries telemetry slices
│   │   ├── regulations.py           # FIA Sporting Regulations & Judicial Code queries
│   │   └── assistant.py             # AI Steward Assistant decision support endpoint
│   ├── core/                        # Global configuration, logging & exceptions
│   │   ├── __init__.py
│   │   ├── config.py                # Pydantic-settings BaseSettings model
│   │   ├── logging.py               # Structured logging configuration
│   │   └── exceptions.py            # AppException hierarchy & standardized JSON error handlers
│   ├── database/                    # SQLAlchemy 2.0 ORM engine & session management
│   │   ├── __init__.py
│   │   ├── base.py                  # DeclarativeBase & TimestampMixin
│   │   └── connection.py            # Engine, SessionLocal, get_db dependency & health probe
│   ├── models/                      # Relational database models (SQLAlchemy 2.0 mapped)
│   │   ├── __init__.py
│   │   ├── race.py                  # Race model
│   │   ├── session.py               # Session model
│   │   ├── driver.py                # Driver model
│   │   ├── incident.py              # Incident evidence candidate model (NO fault/guilt fields)
│   │   ├── incident_driver.py       # IncidentDriver neutral join model (INVOLVED/PRIMARY/SECONDARY)
│   │   ├── telemetry.py             # Telemetry multi-rate normalized record model
│   │   └── regulation.py            # Regulation statutory repository model
│   ├── schemas/                     # Pydantic v2 schemas & request/response contracts
│   │   ├── __init__.py
│   │   ├── common.py                # HealthResponse, PaginationParams, ErrorResponse
│   │   ├── race.py                  # RaceResponse, RaceSessionSchema, RaceListResponse
│   │   ├── session.py               # SessionResponse, SessionSummaryResponse, RaceActivityPoint
│   │   ├── driver.py                # DriverResponse, DriverStats
│   │   ├── incident.py              # IncidentSummary, IncidentDetailResponse, IncidentStatusUpdate
│   │   ├── telemetry.py             # TelemetryPointSchema, TelemetrySliceResponse, TelemetryQueryParams
│   │   ├── regulation.py            # RegulationSchema, RelevantRegulationSchema, EvidenceRegulationConnectionSchema
│   │   └── assistant.py             # AssistantQueryRequest, AssistantMessageSchema, EvidenceChip
│   ├── services/                    # Domain business logic (stubs for Phase 3/4)
│   │   └── __init__.py
│   ├── data/                        # Ingestion package stubs
│   │   ├── __init__.py
│   │   ├── fastf1/                  # FastF1 ingest pipeline (Phase 3)
│   │   │   └── __init__.py
│   │   └── openf1/                  # OpenF1 adapter pipeline (Phase 3)
│   │       └── __init__.py
│   ├── ml/                          # Anomaly detection & trajectory models (Phase 4)
│   │   └── __init__.py
│   ├── evidence/                    # Multi-source evidence synthesizer (Phase 4)
│   │   └── __init__.py
│   ├── evaluation/                  # ML evaluation & benchmark metrics (Phase 4)
│   │   └── __init__.py
│   └── tests/                       # Automated test suite
│       ├── __init__.py
│       ├── conftest.py              # In-memory SQLite fixture & dependency overrides
│       ├── test_app.py              # App initialization, OpenAPI & CORS tests
│       ├── test_config.py           # Configuration loading & validation tests
│       ├── test_database.py         # DB connection diagnostics tests
│       ├── test_health.py           # Diagnostic health endpoint tests
│       ├── test_routes.py           # REST route integration tests
│       └── test_schemas.py          # Pydantic schema constraint tests
```

---

## 2. Files Created

1. `backend/app/__init__.py`
2. `backend/app/main.py`
3. `backend/app/core/__init__.py`
4. `backend/app/core/config.py`
5. `backend/app/core/logging.py`
6. `backend/app/core/exceptions.py`
7. `backend/app/database/__init__.py`
8. `backend/app/database/base.py`
9. `backend/app/database/connection.py`
10. `backend/app/models/__init__.py`
11. `backend/app/models/race.py`
12. `backend/app/models/session.py`
13. `backend/app/models/driver.py`
14. `backend/app/models/incident.py`
15. `backend/app/models/incident_driver.py`
16. `backend/app/models/telemetry.py`
17. `backend/app/models/regulation.py`
18. `backend/app/schemas/__init__.py`
19. `backend/app/schemas/common.py`
20. `backend/app/schemas/race.py`
21. `backend/app/schemas/session.py`
22. `backend/app/schemas/driver.py`
23. `backend/app/schemas/incident.py`
24. `backend/app/schemas/telemetry.py`
25. `backend/app/schemas/regulation.py`
26. `backend/app/schemas/assistant.py`
27. `backend/app/api/__init__.py`
28. `backend/app/api/health.py`
29. `backend/app/api/races.py`
30. `backend/app/api/sessions.py`
31. `backend/app/api/drivers.py`
32. `backend/app/api/incidents.py`
33. `backend/app/api/telemetry.py`
34. `backend/app/api/regulations.py`
35. `backend/app/api/assistant.py`
36. `backend/app/services/__init__.py`
37. `backend/app/data/__init__.py`
38. `backend/app/data/fastf1/__init__.py`
39. `backend/app/data/openf1/__init__.py`
40. `backend/app/ml/__init__.py`
41. `backend/app/evidence/__init__.py`
42. `backend/app/evaluation/__init__.py`
43. `backend/app/tests/__init__.py`
44. `backend/app/tests/conftest.py`
45. `backend/app/tests/test_app.py`
46. `backend/app/tests/test_config.py`
47. `backend/app/tests/test_database.py`
48. `backend/app/tests/test_health.py`
49. `backend/app/tests/test_schemas.py`
50. `backend/app/tests/test_routes.py`
51. `docs/progress/PROMPT_02_REPORT.md`

---

## 3. Files Modified

1. `.env.example`: Expanded with all backend environment variable documentation (`APP_NAME`, `APP_VERSION`, `ENVIRONMENT`, `DEBUG`, `API_V1_PREFIX`, `DATABASE_URL`, `FASTF1_CACHE_DIR`, `OPENF1_BASE_URL`, `LOG_LEVEL`, `CORS_ORIGINS`, `VITE_API_BASE_URL`).

---

## 4. Database Models

The relational schema implements the strict hierarchy:
`Race` $\rightarrow$ `Session` $\rightarrow$ (`Driver`, `Telemetry`, `Incident` $\rightarrow$ `IncidentDriver`), plus normalized `Regulation`:

| Model | Table Name | Key Attributes | Constraints & Indexes | Relationships |
|---|---|---|---|---|
| **`Race`** | `races` | `id` (PK, str), `series`, `season`, `round`, `name`, `circuit`, `country`, `city`, `date`, `source`, `source_id` | `id` index, `series` index, `season` index | `sessions` (1-to-many, cascade delete) |
| **`Session`** | `sessions` | `id` (PK, str), `race_id` (FK), `session_type`, `name`, `date`, `start_time`, `end_time`, `total_laps`, `status`, `source` | `race_id` FK index, `status` index | `race` (many-to-1), `drivers` (1-to-many), `incidents` (1-to-many), `telemetry_records` (1-to-many) |
| **`Driver`** | `drivers` | `id` (PK, str), `session_id` (FK), `code`, `number`, `full_name`, `abbreviation`, `nationality`, `team`, `team_color`, `laps_completed`, `avg_speed_kmh`, `max_speed_kmh` | Unique constraint `(session_id, code)`, `code` index | `session` (many-to-1), `incident_participations` (1-to-many) |
| **`Incident`** | `incidents` | `id` (PK, str), `session_id` (FK), `incident_type`, `status`, `severity`, `lap`, `turn`, `timestamp_str`, `start_time`, `end_time`, `summary`, `detection_method`, `evidence_strength` (0-100), `video_available`, `telemetry_available` | `session_id` FK index, `lap` index, `status` index, `severity` index | `session` (many-to-1), `drivers_involved` via `IncidentDriver` |
| **`IncidentDriver`** | `incident_drivers` | `id` (PK, int), `incident_id` (FK), `driver_id` (FK), `role` (`INVOLVED`, `PRIMARY`, `SECONDARY`) | Unique constraint `(incident_id, driver_id)` | `incident` (many-to-1), `driver` (many-to-1) |
| **`Telemetry`** | `telemetry` | `id` (PK, BigInt), `session_id` (FK), `driver_id` (FK), `timestamp`, `time_offset`, `lap_number`, `distance`, `speed`, `throttle`, `brake`, `steering`, `gear`, `rpm`, `drs`, `accel_x`, `accel_y` | Composite index `(session_id, driver_id, timestamp)`, index `(session_id, lap_number)` | `session` (many-to-1), `driver` (many-to-1) |
| **`Regulation`** | `regulations` | `id` (PK, str), `series`, `season`, `document`, `article`, `title`, `text`, `source_url`, `source` | `article` index, `season` index | None (Independent statutory catalog) |

### Strict Domain Guardrails Maintained:
- **No direct `Incident` $\rightarrow$ `Driver` FK**: All connections route through the `incident_drivers` join table.
- **Zero Guilt/Fault Columns**: Neither `Incident` nor `IncidentDriver` contain `at_fault_driver`, `guilty_driver`, `penalty_driver`, `fault_score`, or `guilt_probability`.
- **Neutral Driver Vocabularies**: Join roles are strictly limited to `INVOLVED`, `PRIMARY`, and `SECONDARY`.
- **Evidence Strength Meaning**: `evidence_strength` denotes algorithmic telemetry correlation, explicitly documented as not representing guilt.

---

## 5. Pydantic Schemas

Schemas were developed using Pydantic v2 with camelCase alias generation (`to_camel`), enabling 100% type-safe serialization matching the frontend TypeScript interfaces:

- **`common.py`**:
  - `HealthResponse`: Diagnostic state covering DB and FastF1 cache.
  - `PaginationParams`: Constrained pagination ($1 \le \text{page}$, $1 \le \text{page\_size} \le 200$).
  - `PaginatedResponse[T]`: Generic container with total count and page calculation.
  - `ErrorDetail` / `ErrorResponse`: Structured, machine-readable error payload.
- **`race.py`**:
  - `RaceResponse`: Complete Grand Prix representation with `sessions`, dates, and track metadata.
  - `RaceSessionSchema`: Sub-session schedule and status.
- **`session.py`**:
  - `SessionResponse`: Session details.
  - `SessionSummaryResponse`: Feeds the 4 dashboard metric cards and pipeline status indicators.
  - `RaceActivityPoint`: Feeds the Recharts incident density bar chart across laps.
- **`driver.py`**:
  - `DriverResponse`: Driver livery, team colors, and statistics.
  - `DriverStats`: Session telemetry aggregate statistics.
- **`incident.py`**:
  - `IncidentSummary`: Lightweight model for the Incident Explorer table.
  - `IncidentDetailResponse`: 8-part evidence dossier matching `IncidentDetailView`.
  - `TimeWindow`: Microsecond start/end timestamps.
  - `IncidentStatusUpdate`: Validated steward review transition payload.
- **`telemetry.py`**:
  - `TelemetryPointSchema`: Synchronized time frame (Speed, Pedals, Steering, Gear, Accel, Gap, Closing Velocity).
  - `TelemetrySliceResponse`: Bounded multi-channel slice container.
  - `TelemetryQueryParams`: Bounded query model enforcing safety caps ($\le 2000$ points) to prevent accidental database dumps.
- **`regulation.py`**:
  - `RegulationSchema`: Normalized statutory text record.
  - `RelevantRegulationSchema`: Contextual regulation match with match reasoning and relevance rating.
  - `EvidenceRegulationConnectionSchema`: 3-way link (`Observed Evidence` $\rightarrow$ `Relevant Regulation` $\rightarrow$ `Steward Review Action`).
- **`assistant.py`**:
  - `AssistantQueryRequest`: Validated steward inquiry text.
  - `AssistantMessageSchema`: Structured response with `evidenceChips`, `evidenceLinks`, and suggested follow-ups.

---

## 6. API Endpoints Implemented

All 17 target endpoints are fully implemented and registered under `/api/v1`:

| Method | Route | Handler Module | Status |
|---|---|---|---|
| `GET` | `/` | `app.main:root` | **Operational** (200 OK service discovery) |
| `GET` | `/api/v1/health` | `app.api.health:get_health` | **Operational** (Diagnostics & degraded fallback) |
| `GET` | `/api/v1/races` | `app.api.races:get_races` | **Operational** (DB query with season filter) |
| `GET` | `/api/v1/races/{race_id}` | `app.api.races:get_race` | **Operational** (DB query or 404) |
| `GET` | `/api/v1/sessions/{session_id}` | `app.api.sessions:get_session` | **Operational** (DB query or 404) |
| `GET` | `/api/v1/sessions/{session_id}/summary` | `app.api.sessions:get_session_summary` | **Operational** (DB aggregate metrics or 404) |
| `GET` | `/api/v1/sessions/{session_id}/activity`| `app.api.sessions:get_session_activity`| **Operational** (DB lap aggregation or 404) |
| `GET` | `/api/v1/sessions/{session_id}/drivers` | `app.api.sessions:get_session_drivers` | **Operational** (DB query or 404) |
| `GET` | `/api/v1/drivers` | `app.api.drivers:get_drivers` | **Operational** (DB query with deduplication) |
| `GET` | `/api/v1/drivers/{code}` | `app.api.drivers:get_driver` | **Operational** (DB query by 3-letter code or 404) |
| `GET` | `/api/v1/incidents` | `app.api.incidents:get_incidents` | **Operational** (DB query with multi-filtering) |
| `GET` | `/api/v1/incidents/{incident_id}` | `app.api.incidents:get_incident` | **Operational** (DB query or 404) |
| `PATCH`| `/api/v1/incidents/{incident_id}/status`| `app.api.incidents:update_incident_status`| **Operational** (Status update & DB commit) |
| `GET` | `/api/v1/incidents/{incident_id}/telemetry`| `app.api.telemetry:get_incident_telemetry`| **Operational** (Bounded slice contract or 404) |
| `GET` | `/api/v1/regulations` | `app.api.regulations:get_regulations` | **Operational** (DB query with search filter) |
| `GET` | `/api/v1/regulations/{regulation_id}`| `app.api.regulations:get_regulation` | **Operational** (DB query or 404) |
| `POST` | `/api/v1/assistant/query` | `app.api.assistant:query_assistant` | **Operational** (Context-aware inquiry processor) |

---

## 7. Endpoints Intentionally Deferred

To prevent fake production data from contaminating the codebase:
- **Full Historical FastF1 Telemetry Population**: Telemetry endpoints currently return the verified, bounded schema with 0 rows or seeded data. Heavy background session ingest is deferred to Phase 3.
- **Automated ML Anomaly Inference**: The incident detection pipeline (`app/ml/`) is intentionally stubbed for Phase 4 so proper training sets and evaluation baselines can be built first.
- **Embedding/Vector RAG Search**: Regulations are currently queried via exact and keyword ILIKE search. Vector similarity retrieval is deferred until the regulatory corpus is fully indexed.

---

## 8. Configuration Variables

Defined in `app/core/config.py` using `pydantic-settings`:

| Key | Type | Default | Description |
|---|---|---|---|
| `APP_NAME` | `str` | `"Motorsport Incident Intelligence API"` | Human-readable service title |
| `APP_VERSION` | `str` | `"1.0.0"` | Current API version |
| `ENVIRONMENT` | `str` | `"development"` | Environment tag (`development`, `staging`, `production`) |
| `DEBUG` | `bool` | `False` | Debug mode toggle |
| `API_V1_PREFIX` | `str` | `"/api/v1"` | URL prefix for REST routes |
| `DATABASE_URL` | `str` | `"postgresql+psycopg://postgres:postgres@localhost:5432/motorsport_intelligence"` | PostgreSQL connection string |
| `FASTF1_CACHE_DIR` | `str` | `"data/cache/fastf1"` | Local filesystem path for FastF1 cache |
| `OPENF1_BASE_URL` | `str` | `"https://api.openf1.org/v1"` | OpenF1 endpoint root |
| `LOG_LEVEL` | `str` | `"INFO"` | Minimum logging threshold |
| `CORS_ORIGINS` | `list[str]` | `["http://localhost:3000", ...]` | Permitted CORS browser origins |

---

## 9. Error Handling Approach

- **Custom Exception Hierarchy**: `AppException` base class with specialized sub-exceptions: `ResourceNotFoundException` (404), `ValidationException` (422), and `DatabaseConnectionException` (503).
- **Uniform Error Envelope**:
  ```json
  {
    "error": {
      "code": "RESOURCE_NOT_FOUND",
      "message": "Race with ID 'xyz' was not found.",
      "status_code": 404,
      "details": { "resource_type": "Race", "resource_id": "xyz" }
    }
  }
  ```
- **Zero Stack Traces Leaked**: Internal exceptions are logged with full tracebacks on the server while the client receives a secure, generic 500 error envelope.

---

## 10. CORS Configuration

- Configured in `app/main.py` using `CORSMiddleware`.
- Development defaults explicitly allow:
  - `http://localhost:3000` (Vite dev server)
  - `http://127.0.0.1:3000`
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
- Allowed HTTP Methods: `GET`, `POST`, `PATCH`, `DELETE`, `OPTIONS`.
- Wildcard `*` origins are strictly avoided.

---

## 11. Tests Created

Automated test suite under `backend/app/tests/`:
1. `test_app.py`: Tests root endpoint (`/`), OpenAPI schema validation (`/openapi.json`), and CORS preflight options.
2. `test_config.py`: Tests default settings, comma-separated CORS parsing, and cached singleton behavior.
3. `test_database.py`: Tests connection probe signature and non-crashing operational behavior.
4. `test_health.py`: Tests `/api/v1/health` response structure and cache directory readiness.
5. `test_schemas.py`: Tests valid/invalid telemetry frames, safety limits on query caps, assistant validation, and camelCase serialization.
6. `test_routes.py`: Tests empty list returns, structured 404 errors, assistant queries, and 422 validation errors.

---

## 12. Test Results

Executed via:
```powershell
$env:PYTHONPATH="backend"; python -m pytest backend/app/tests -v
```

**Results:**
```
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0
collected 24 items

backend/app/tests/test_app.py::test_root_endpoint PASSED                 [  4%]
backend/app/tests/test_app.py::test_openapi_schema PASSED                [  8%]
backend/app/tests/test_app.py::test_cors_headers PASSED                  [ 12%]
backend/app/tests/test_config.py::test_default_settings PASSED           [ 16%]
backend/app/tests/test_config.py::test_cors_origins_parsing PASSED       [ 20%]
backend/app/tests/test_config.py::test_get_settings_cached PASSED        [ 25%]
backend/app/tests/test_database.py::test_check_db_connection_signature PASSED [ 29%]
backend/app/tests/test_health.py::test_health_endpoint PASSED            [ 33%]
backend/app/tests/test_routes.py::test_get_races_empty PASSED            [ 37%]
backend/app/tests/test_routes.py::test_get_race_not_found PASSED         [ 41%]
backend/app/tests/test_routes.py::test_get_session_not_found PASSED      [ 45%]
backend/app/tests/test_routes.py::test_get_drivers_empty PASSED          [ 50%]
backend/app/tests/test_routes.py::test_get_driver_not_found PASSED       [ 54%]
backend/app/tests/test_routes.py::test_get_incidents_empty PASSED        [ 58%]
backend/app/tests/test_routes.py::test_get_incident_not_found PASSED     [ 62%]
backend/app/tests/test_routes.py::test_get_incident_telemetry_not_found PASSED [ 66%]
backend/app/tests/test_routes.py::test_get_regulations_empty PASSED      [ 70%]
backend/app/tests/test_routes.py::test_assistant_query PASSED            [ 75%]
backend/app/tests/test_routes.py::test_update_incident_status_invalid PASSED [ 79%]
backend/app/tests/test_schemas.py::test_telemetry_point_valid PASSED     [ 83%]
backend/app/tests/test_schemas.py::test_telemetry_point_invalid_throttle PASSED [ 87%]
backend/app/tests/test_schemas.py::test_telemetry_query_params_safety_limit PASSED [ 91%]
backend/app/tests/test_schemas.py::test_assistant_query_request_validation PASSED [ 95%]
backend/app/tests/test_schemas.py::test_race_response_camel_case PASSED  [100%]

======================= 24 passed in 9.08s ========================
```

---

## 13. FastAPI Startup Result

Verified through Python ASGI execution with live requests:
- Root route `GET /` returns `200 OK` with operational metadata.
- Lifespan context manager starts cleanly, loads settings, initializes structured logging, and registers middleware without warnings.

---

## 14. Health Endpoint Result

Request: `GET /api/v1/health`  
Status: `200 OK`  
Payload:
```json
{
  "status": "degraded",
  "appName": "Motorsport Incident Intelligence API",
  "appVersion": "1.0.0",
  "environment": "development",
  "apiPrefix": "/api/v1",
  "databaseConnected": false,
  "fastf1CacheReady": true,
  "fastf1CacheDir": "data\\cache\\fastf1",
  "timestamp": "2026-09-27T08:09:06.696255Z"
}
```
*Note*: When PostgreSQL is not running locally, the endpoint returns `status: degraded` and `databaseConnected: false` gracefully without hanging or throwing unhandled 500 errors.

---

## 15. OpenAPI Result

Request: `GET /openapi.json`  
Status: `200 OK`  
Generated Schema Details:
- OpenAPI Specification Version: `3.1.0`
- Registered Path Count: 17 endpoints
- Documentation UI: Accessible at `/docs` (Swagger UI) and `/redoc` (ReDoc)

---

## 16. Unresolved Issues

None. All Phase 2 foundation requirements are fully satisfied. The frontend build remains pristine (`npm run build` completed in ~14s with 0 errors).

---

## 17. Recommended Next Step for Prompt 3

**Prompt 03 — FastF1 Data Ingestion & Session Normalization Engine**:
1. Implement `FastF1Service` under `backend/app/data/fastf1/service.py` to ingest official F1 championship calendars, sessions, laps, and driver metadata.
2. Build session ingestion CLI/script to populate SQLite/PostgreSQL with the 2024 Italian Grand Prix (Monza) event, sessions, and calibrated driver roster.
3. Implement 25Hz telemetry resampling and relative pair association algorithms to calculate closing speeds, gap deltas, and lateral motion without confusing normal racing proximity with incidents.
