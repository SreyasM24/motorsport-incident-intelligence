# REST API Specification

Motorsport Incident Intelligence provides a RESTful API built on FastAPI. All API endpoints return JSON responses conforming to OpenAPI 3.1 standards.

Base URL: `/api/v1`

---

## 1. System & Health Endpoints

### `GET /health`
Returns system status, active database connectivity, cache hit ratios, and worker states.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "app": "Motorsport Incident Intelligence API",
  "version": "1.0.0",
  "database": "connected",
  "cache": {
    "dossier_entries": 4,
    "hit_ratio": 0.82
  },
  "timestamp": "2026-09-29T08:00:00Z"
}
```

---

## 2. Session Management

### `GET /api/v1/sessions`
Retrieves all recorded Grand Prix sessions.

**Query Parameters**:
- `year` (optional, integer): Filter by Championship year (e.g. `2024`).
- `circuit` (optional, string): Filter by circuit identifier (e.g. `monza`, `red_bull_ring`).

**Response `200 OK`**:
```json
[
  {
    "id": "monza_2024_race",
    "year": 2024,
    "round": 16,
    "circuit_name": "Autodromo Nazionale Monza",
    "session_type": "Race",
    "official_date": "2024-09-01",
    "total_laps": 53
  }
]
```

---

## 3. Incident Candidates

### `GET /api/v1/incidents`
Lists detected incident candidates across sessions.

**Query Parameters**:
- `session_id` (optional, string): Filter by session identifier.
- `status` (optional, string): Filter by review status (`pending`, `reviewed`, `escalated`).

**Response `200 OK`**:
```json
[
  {
    "id": "cand_monza_lap15_ric_hul",
    "session_id": "monza_2024_race",
    "lap": 15,
    "corner": "Variante Ascari (T8-T9)",
    "car_primary": "3",
    "car_secondary": "27",
    "driver_primary": "RIC",
    "driver_secondary": "HUL",
    "timestamp_utc": "2024-09-01T13:32:14.200Z",
    "review_status": "reviewed"
  }
]
```

---

## 4. Overtake & Telemetry Analysis

### `GET /api/v1/analysis/telemetry/{incident_id}`
Returns the synchronized 25Hz telemetry stream for the cars involved in the incident window.

**Response `200 OK`**:
```json
{
  "incident_id": "cand_monza_lap15_ric_hul",
  "hz": 25,
  "window_seconds": 6.0,
  "frames": [
    {
      "time_offset_ms": -1200,
      "car_primary": {
        "speed_kmh": 284.2,
        "throttle": 0.0,
        "brake": 100.0,
        "gear": 6,
        "steering_angle_deg": -4.2,
        "lat_accel_g": 0.32,
        "long_accel_g": -4.85
      },
      "car_secondary": {
        "speed_kmh": 289.1,
        "throttle": 0.0,
        "brake": 95.0,
        "gear": 6,
        "steering_angle_deg": -1.1,
        "lat_accel_g": 0.15,
        "long_accel_g": -4.62
      }
    }
  ]
}
```

### `GET /api/v1/analysis/overtake-geometry/{incident_id}`
Returns calculated spatial clearances, corner phases, and trajectory convergence metrics.

**Response `200 OK`**:
```json
{
  "incident_id": "cand_monza_lap15_ric_hul",
  "phases": {
    "entry": {
      "overlap_pct": 78.4,
      "lateral_clearance_meters": 2.15,
      "longitudinal_delta_meters": 1.2
    },
    "apex": {
      "overlap_pct": 52.1,
      "lateral_clearance_meters": 0.42,
      "relative_velocity_kmh": 6.4
    },
    "exit": {
      "overlap_pct": 14.0,
      "lateral_clearance_meters": 0.18,
      "trajectory_divergence_angle_deg": 14.8
    }
  }
}
```

---

## 5. Evidence Dossiers

### `GET /api/v1/dossier/{incident_id}`
Retrieves the comprehensive synthesized multi-modal evidence dossier.

**Response `200 OK`**:
```json
{
  "dossier_id": "dossier_monza_lap15_ric_hul",
  "incident_id": "cand_monza_lap15_ric_hul",
  "provenance_hash": "sha256-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "telemetry_summary": {
    "car_primary_braking_delta_meters": 12.4,
    "car_secondary_braking_delta_meters": -1.2,
    "peak_lateral_accel_g": 3.9
  },
  "geometry_summary": {
    "min_lateral_clearance_meters": 0.38,
    "apex_overlap_pct": 52.1
  },
  "cv_summary": {
    "visual_overlap_observed": true,
    "visual_contact_detected": true,
    "detection_confidence": 0.94
  },
  "discrepancies": [
    {
      "type": "TELEMETRY_VS_VISUAL_CONTACT",
      "severity": "LOW",
      "description": "Visual bounding box overlap observed at T+1.2s with small 0.8g lateral impulse in telemetry."
    }
  ],
  "regulatory_citations": [
    {
      "code": "ISC-APP-L-CH4-ART2B",
      "title": "Overtaking & Car Control Guidelines",
      "summary": "Driver being overtaken must leave at least one car width if inside car has substantial overlap before apex."
    }
  ]
}
```

---

## 6. Steward Review Workflow

### `POST /api/v1/stewards/review`
Submits a licensed human steward review assessment.

**Request Body**:
```json
{
  "incident_id": "cand_monza_lap15_ric_hul",
  "steward_name": "Chief Steward",
  "review_status": "reviewed",
  "dossier_hash_acknowledged": "sha256-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "steward_notes": "Telemetry confirms Car 27 was significantly alongside at apex. Car 3 failed to maintain racing room on exit.",
  "concurrence_status": "CONCURRED"
}
```

**Response `201 Created`**:
```json
{
  "review_id": "rev_20240901_001",
  "status": "persisted",
  "timestamp": "2026-09-29T08:15:32Z"
}
```

---

## 7. Citation-Grounded Evidence & Knowledge Retrieval (Prompt 21)

### `GET /api/v1/evidence/regulations/search`
Retrieves citation-grounded regulatory passages from canonical FIA sporting regulations and Driving Standards Guidelines.

**Query Parameters**:
- `query` (required, string): Natural-language or statutory query (e.g. `leaving room on exit`).
- `season` (optional, integer, default `2024`): Championship season filter.
- `method` (optional, string, default `hybrid`): Retrieval strategy (`lexical`, `semantic`, `hybrid`).
- `case_date` (optional, string): Incident ISO date (`YYYY-MM-DD`) for temporal applicability filtering.
- `article_filter` (optional, string): Substring filter for article numbers (e.g. `33.3`).
- `limit` (optional, integer, default `5`): Maximum citations to return.

**Response `200 OK`**:
```json
{
  "queryInterpreted": "leaving room on exit",
  "totalFound": 3,
  "citations": [
    {
      "claim": "Potentially applicable regulatory provision for observed racing engagement.",
      "source": "FIA World Motor Sport Council",
      "documentName": "FIA Formula One Sporting Regulations 2024",
      "articleNumber": "Article 33.3",
      "heading": "Track Limits and Leaving the Track",
      "verbatimText": "Drivers must make every reasonable effort to use the track at all times...",
      "relevanceScore": 0.88,
      "retrievalMethod": "HYBRID_LEXICAL_SEMANTIC",
      "provenanceStatus": "AUTHORITATIVE",
      "epistemicNotice": "CRITICAL NOTICE: Regulatory citations are documentary references only..."
    }
  ],
  "conflicts": [],
  "effectiveDateFilterApplied": false,
  "seasonFilterApplied": true,
  "nonAdjudicationStatement": "CRITICAL NON-ADJUDICATIVE NOTICE: Regulatory citations are documentary references only."
}
```

### `GET /api/v1/evidence/historical/search`
Searches verified historical incident records based purely on observable kinematics with precedent isolation.

**Query Parameters**:
- `query` (optional, string): Observable description query.
- `case_id` (optional, string): Benchmark case identifier to find kinematically comparable matches for.
- `circuit` (optional, string): Circuit filter.
- `category` (optional, string): Interaction category filter (e.g. `FORCING_OFF_TRACK`).
- `top_k` (optional, integer, default `5`): Maximum cases to return.

### `GET /api/v1/evidence/documents/{document_id}`
Returns full document metadata and registered child chunks.

### `GET /api/v1/evidence/documents/{document_id}/chunks/{chunk_id}`
Returns atomic chunk text, article number, and cryptographic SHA-256 hash.

### `GET /api/v1/evidence/retrieval/benchmark`
Executes the gold retrieval evaluation benchmark and returns Precision@k, Recall@k, and MRR.

### `GET /api/v1/evidence/integrity`
Audits document SHA-256 hashes and confirms zero orphaned text chunks.
