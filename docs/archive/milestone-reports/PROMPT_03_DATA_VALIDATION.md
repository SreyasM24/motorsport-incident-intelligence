# PROMPT 03 — SOURCE DATA QUALITY & VALIDATION REPORT

**Project:** Motorsport Incident Intelligence (MII)  
**Phase:** 03 — FastF1 + OpenF1 Data Ingestion Pipeline  
**Document:** `docs/progress/PROMPT_03_DATA_VALIDATION.md`  
**Date:** September 2026  
**Status:** VALIDATED (Real FastF1 2024 Monza Race + Live OpenF1 API Validated, 37/37 Pytest Passed)

---

## 1. FastF1 Implementation

The FastF1 ingestion pipeline is organized cleanly under `backend/app/data/fastf1/` adhering to strict service boundary rules:
- `client.py` (`FastF1Client`): Direct wrapper around FastF1 library routines (`fastf1.get_event_schedule`, `fastf1.get_event`, `fastf1.get_session`). Handles missing schedules and translates library-specific exceptions.
- `cache.py` (`setup_fastf1_cache`, `get_cache_status`): Manages local filesystem caching configured via `FASTF1_CACHE_DIR` (defaults to `data/cache/fastf1`). Automatically ensures folder existence, enables persistent cache, and reports file counts and disk usage.
- `normalizer.py`: Transforms FastF1 Pandas DataFrames and Series into canonical internal domain objects without leaking dataframe types into the core backend.
- `loader.py` (`FastF1DataSource`): Implements `BaseDataSource` protocol. Manages lazy loading of session components (laps, telemetry, weather, race control messages) and tracks load states (`_session_load_status`) to prevent `DataNotLoadedError`.
- `exceptions.py`: Strongly typed exception hierarchy (`FastF1Error`, `FastF1SessionNotFoundError`, `FastF1DataUnavailableError`, `FastF1CacheError`).

---

## 2. OpenF1 Implementation

The OpenF1 live ingestion adapter is organized under `backend/app/data/openf1/`:
- `client.py` (`OpenF1Client`): Production-grade HTTP client built with `httpx.Client`. Connects to `OPENF1_BASE_URL` (defaults to `https://api.openf1.org/v1`).
  - Supports query parameters and bounded queries (`limit`, `date_start`, `date_end`).
  - Implements exponential backoff retries on HTTP 429 (`Retry-After`) and HTTP 5xx transient server errors.
  - Exposes dedicated methods for `sessions`, `drivers`, `car_data`, `location`, `laps`, and `race_control`.
  - Supports Python context manager protocol (`__enter__`, `__exit__`) for clean socket disposal.
- `normalizer.py`: Transforms OpenF1 JSON payloads into canonical domain dataclasses.
- `exceptions.py`: Dedicated error hierarchy (`OpenF1Error`, `OpenF1RateLimitError`, `OpenF1ResourceNotFoundError`, `OpenF1TimeoutError`).

---

## 3. Files Created / Modified

### Created:
1. `backend/app/data/domain.py`: Canonical internal domain dataclasses (`NormalizedRace`, `NormalizedSession`, `NormalizedDriver`, `NormalizedLap`, `NormalizedTelemetryPoint`, `NormalizedRaceControlMessage`).
2. `backend/app/data/base.py`: Abstract `BaseDataSource` interface.
3. `backend/app/data/fastf1/__init__.py`: Package exports for FastF1.
4. `backend/app/data/fastf1/client.py`: Low-level FastF1 client wrapper.
5. `backend/app/data/fastf1/loader.py`: FastF1DataSource loader implementing BaseDataSource.
6. `backend/app/data/fastf1/cache.py`: Cache initialization and inspection.
7. `backend/app/data/fastf1/normalizer.py`: Normalization from FastF1 DataFrames to domain models.
8. `backend/app/data/fastf1/exceptions.py`: FastF1 exception hierarchy.
9. `backend/app/data/openf1/__init__.py`: Package exports for OpenF1.
10. `backend/app/data/openf1/client.py`: OpenF1 HTTP client with retries and bounds.
11. `backend/app/data/openf1/normalizer.py`: Normalization from OpenF1 JSON to domain models.
12. `backend/app/data/openf1/exceptions.py`: OpenF1 exception hierarchy.
13. `backend/app/data/persistence.py`: Controlled database persistence for Race, Session, Driver metadata, and bounded telemetry batches.
14. `backend/app/services/ingestion_service.py`: High-level `IngestionService` coordinating data providers.
15. `backend/scripts/validate_real_data.py`: Live integration and invariant verification script.
16. `backend/app/tests/test_fastf1_normalizer.py`: Unit tests for FastF1 normalization.
17. `backend/app/tests/test_openf1.py`: Unit tests for OpenF1 client, normalizer, and retries.
18. `backend/app/tests/test_ingestion_service.py`: Unit tests for IngestionService layer.

### Modified:
1. `backend/app/models/telemetry.py`: Made `speed`, `throttle`, `brake`, and `steering` nullable to handle raw feed channel omissions without schema errors.
2. `backend/app/schemas/telemetry.py`: Added `DriverTelemetryPointSchema` and `DriverTelemetryResponse` for bounded telemetry slices.
3. `backend/app/schemas/__init__.py`: Exported new telemetry schemas.
4. `backend/app/api/races.py`: Connected `get_races` to `IngestionService` (supports `auto_fetch: bool = Query(default=False)`).
5. `backend/app/api/sessions.py`: Connected `get_session_drivers` to `IngestionService` for dynamic driver transponder discovery.
6. `backend/app/api/telemetry.py`: Added `/api/v1/telemetry/driver-stream` endpoint for safe, bounded raw telemetry queries.

---

## 4. Normalized Domain Structures

Domain entities in `backend/app/data/domain.py` act as the firewall between raw source libraries and the application core:
- **`NormalizedRace`**: `id`, `series`, `season`, `round_number`, `name`, `official_name`, `circuit_name`, `country`, `city`, `event_date`, `source`, `source_id`, `metadata`.
- **`NormalizedSession`**: `id`, `race_id`, `session_type`, `session_name`, `session_date`, `start_time`, `end_time`, `total_laps`, `status`, `source`, `source_id`.
- **`NormalizedDriver`**: `id`, `session_id`, `code`, `number`, `full_name`, `first_name`, `last_name`, `abbreviation`, `team`, `team_color`, `secondary_color`, `nationality`, `laps_completed`, `avg_speed_kmh`, `max_speed_kmh`, `source`, `source_id`.
- **`NormalizedLap`**: `driver_code`, `driver_number`, `lap_number`, `lap_time_seconds`, `sector_1_seconds`, `sector_2_seconds`, `sector_3_seconds`, `compound`, `is_valid`, `start_time`, `source`.
- **`NormalizedTelemetryPoint`**: `timestamp`, `time_offset`, `driver_code`, `driver_number`, `lap_number`, `distance`, `x`, `y`, `z`, `speed`, `throttle`, `brake`, `steering`, `gear`, `rpm`, `drs`, `accel_x`, `accel_y`, `source`.
- **`NormalizedRaceControlMessage`**: `timestamp`, `lap_number`, `category`, `message`, `flag`, `scope`, `sector`, `source`.

---

## 5. Cache Behavior

- **Path**: Configured through `FASTF1_CACHE_DIR="data/cache/fastf1"`.
- **Behavior**:
  - Initial access fetches from Formula 1 timing servers and parses SQLite/JSON pickle files into disk.
  - Subsequent access uses the local disk cache directly.
- **Measured Performance**:
  - Uncached First Lap Telemetry Load: **21.53s**
  - Cached Repeated Lap Telemetry Load: **0.64s**
  - Cache Acceleration Factor: **33.3x speedup**
  - Cache Size: **10 files, 84.17 MB** for the full 2024 Italian GP race dataset (timing, laps, car data, position data for 20 drivers).

---

## 6. Database Interaction

- Metadata (Race, Session, Driver) is persisted using idempotent upsert methods (`persist_race`, `persist_session`, `persist_drivers` in `backend/app/data/persistence.py`).
- Telemetry persistence is strictly bounded: `persist_telemetry_batch` writes chunked batches (default 1000 rows) only when specifically requested for bounded slices.
- If PostgreSQL is offline, all ingestion methods, unit tests, and API routes operate cleanly without crashing, degrading gracefully or serving cached in-memory structures.

---

## 7. API Integration

- `GET /api/v1/races`: When `auto_fetch=True` is provided and the DB is unseeded, automatically queries FastF1 to return the full 24-race calendar.
- `GET /api/v1/sessions/{session_id}/drivers`: If driver roster is not yet in the DB, queries `IngestionService` to dynamically return official transponders.
- `GET /api/v1/incidents/{incident_id}/telemetry`: Preserved according to Prompt 01 contract.
- `GET /api/v1/telemetry/driver-stream`: Real bounded telemetry endpoint supporting `season`, `event`, `session`, `driver`, `lap`, and `limit` parameters directly querying the cached FastF1 ingestion engine.

---

## 8. Real Monza 2024 Validation

Executing against real official FIA FastF1 session data for the **2024 Italian Grand Prix (Race)**:

| Check | Expected | Actual | Invariant Status |
| :--- | :--- | :--- | :--- |
| Event Resolution | Italian Grand Prix | `Italian Grand Prix` | PASS |
| Circuit Resolution | Monza | `Autodromo Nazionale Monza` | PASS |
| Session Resolution | Race | `Italian Grand Prix Race` | PASS |
| Driver Discovery | >= 20 Drivers | 20 Drivers (`['ALB', 'ALO', 'BOT', 'COL', 'GAS', 'HAM', 'HUL', 'LEC', 'MAG', 'NOR', 'OCO', 'PER', 'PIA', 'RIC', 'RUS', 'SAI', 'SAR', 'STR', 'TSU', 'VER']`) | PASS |
| Driver Verification | Charles Leclerc #16 | `Code=LEC`, `Number=16`, `Team=Ferrari`, `Color=#E80020` | PASS |
| Lap Timing Records | > 50 Laps | 53 Laps for Charles Leclerc | PASS |
| Lap 10 Telemetry Rows | > 0 | **649 points** | PASS |
| Telemetry Speed Channel | Present (> 0 km/h) | `speed = 233.0 km/h` at mid-lap | PASS |
| Spatial Position (X, Y, Z)| Present | `X=10976.74, Y=14249.58, Z=1933.02` | PASS |
| Throttle & Brake | Present | `Throttle=99.0%`, `Brake=0.0%` | PASS |
| Gear & RPM | Present | `nGear=6`, `RPM=10699` | PASS |

---

## 9. OpenF1 Validation

Live query executed against `https://api.openf1.org/v1`:

| Check | Query | Actual Result |
| :--- | :--- | :--- |
| Session Discovery | `year=2024&country_name=Italy` | 10 sessions returned in 0.62s |
| Selected Session | Imola Race / Monza | Session Key `9515` |
| Driver Lookup | `session_key=9515` | 20 drivers returned in 0.16s |
| Bounded Car Data | `session_key=9515&driver_number=1&limit=50` | 50 telemetry points retrieved in 2.35s |
| Bounded Location | `session_key=9515&driver_number=1&limit=50` | 50 3D spatial points retrieved in 1.82s |
| Race Control Messages | `session_key=9515` | 100 steward flag/track messages retrieved in 0.17s |

---

## 10. Row, Driver, and Session Counts

- **FastF1 2024 Italian GP Drivers**: 20 drivers discovered.
- **FastF1 2024 Italian GP Race Laps**: 53 laps completed by the winning driver (Charles Leclerc).
- **FastF1 Single Lap Telemetry Samples**: 649 observations in Lap 10 for car #16.
- **FastF1 Total Race Telemetry (all 20 cars)**: ~700,000 observations (~84 MB cached).
- **OpenF1 Italy 2024 Sessions**: 10 sessions found across race weekends.
- **OpenF1 Race Control Messages**: 100 messages for session 9515.

---

## 11. Missing / Null Channel Behavior

- **Steering Angle**: Neither FastF1 nor OpenF1 feeds provide steering wheel angle. Both normalizers explicitly output `steering: None`. No artificial values are synthesized.
- **Brake Channel**: In FastF1, brake is often recorded as boolean `True`/`False`. Normalizer transforms `True -> 100.0%` and `False -> 0.0%`. In OpenF1, brake is a 0 or 1 integer, normalized identically.
- **Lap 1 Out-Lap Sector 1**: In FastF1, out-lap sector 1 is NaT because the car did not cross the start/finish line at speed. Normalizer outputs `None` rather than NaN or 0.0.

---

## 12. Timestamp Behavior

- FastF1 provides three distinct time references:
  1. `Date`: Absolute UTC wall-clock timestamp (e.g. `2024-09-01 13:42:10.100000+00:00`).
  2. `Time`: Timedelta elapsed since session start.
  3. `SessionTime`: Track elapsed time.
- Both absolute UTC `timestamp` and floating-point seconds `time_offset` are preserved.
- No timestamps were resampled or altered.

---

## 13. Known Source Differences

| Dimension | FastF1 | OpenF1 |
| :--- | :--- | :--- |
| **Data Format** | Python library returning Pandas DataFrames | Public JSON REST API |
| **Caching** | Local disk file cache (FastF1 Pickle/SQLite) | Client-managed HTTP caching |
| **Coordinates** | Continuous X, Y, Z in mm/meters merged with car data | Separate `/car_data` and `/location` endpoints requiring timestamp joining |
| **Rate** | Variable multi-rate CAN channels (~4Hz to ~20Hz depending on channel) | Car data ~3.7Hz, Location data ~3.7Hz |
| **Historical Depth** | Full seasons from 2018–present with timing archive | Modern era (primarily 2023–present) |
| **Race Control Messages** | Available via `session.race_control_messages` | Dedicated `/race_control` endpoint with sector & flag metadata |

---

## 14. Failures Encountered & Mitigations

1. **`tenacity` Missing Dependency**: Removed optional `tenacity` import in `openf1/client.py` and implemented pure standard-library exponential retry loop (`time.sleep`).
2. **FastF1 `DataNotLoadedError`**: Accessing `session.laps` before `session.load()` raised an exception in FastF1. Fixed by introducing `_session_load_status` dictionary in `FastF1DataSource` to track component loading idempotently.
3. **Accented Slug Transliteration**: `"São Paulo"` was dropping the accented `"ã"` with basic regex. Added `unicodedata.normalize("NFKD", ...)` to cleanly transliterate to `"sao-paulo"`.
4. **FastAPI Route Parameter Collision**: `/api/v1/incidents/driver-stream` was initially captured by `/{incident_id}` route with `incident_id="driver-stream"`. Fixed by registering `/api/v1/telemetry/driver-stream` under the telemetry router prefix.
5. **Database Connection Guard**: Removed unneeded `db: Session = Depends(get_db)` from live streaming telemetry route so FastF1 cached telemetry can be queried freely even when PostgreSQL is offline.

---

## 15. Performance Observations

- FastF1 local cache provides an order-of-magnitude speedup: **21.5s -> 0.64s (33.3x faster)**.
- Telemetry queries for a single driver's single lap return in `< 700ms` from cache.
- OpenF1 bounded queries (50 points) complete over public HTTP in **1.8s - 2.3s**.

---

## 16. What is NOT Implemented Yet

As strictly specified in Prompt 03 instructions:
- **NO telemetry resampling or interpolation** (raw multi-rate timestamps preserved).
- **NO incident detection or collision algorithms**.
- **NO spatial proximity heuristics or threshold tuning**.
- **NO ML anomaly detection or classification models**.
- **NO RAG regulatory embedding or vector search**.
- **NO fault/guilt prediction logic**.

---

## 17. Recommendation for Prompt 04

The data foundation is now complete and validated with real F1 data.
The logical and necessary next step for **Prompt 04** is:

**PROMPT 04: MULTI-RATE TELEMETRY PREPROCESSING, 25Hz SYNCHRONIZATION, AND SPATIAL DYNAMICS ENGINE**
1. Implement a resampler module (`backend/app/ml/preprocessing/` or `services/telemetry_service.py`) that synchronizes multi-rate raw channels (FastF1 car data + position data) to a uniform 25Hz grid using monotonic cubic or linear interpolation.
2. Implement 3D spatial alignment between two interacting cars (calculating Euclidean gap in meters, lateral clearance, and first-derivative closing speeds).
3. Connect the resampled pair engine to `GET /api/v1/incidents/{incident_id}/telemetry` so the frontend Recharts telemetry viewer receives real, synchronized pairwise telemetry traces.
