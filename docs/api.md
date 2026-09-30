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

---

## 7. Computer Vision & Real-World Video Evaluation Endpoints (Prompt 22)

### `GET /api/v1/analysis/cv/dataset`
Retrieves the canonical catalog of video dataset records, legal authorization statuses, and split distributions from `data/cv/real_video_manifest.json`.

**Response `200 OK`**:
```json
{
  "manifestVersion": "2.0",
  "datasetName": "Motorsport Video & Computer Vision Evaluation Dataset",
  "description": "Canonical catalog of real-world, research, and synthetic video records for motorsport CV evaluation.",
  "realWorldVideoStatus": "INSUFFICIENT_DATA",
  "licensePolicy": "Strict copyright compliance: Official Formula One Management (FOM) broadcast footage is commercially copyrighted...",
  "totalVideos": 12,
  "totalDurationSeconds": 248.5,
  "byAuthorizationStatus": {
    "UNAVAILABLE": 6,
    "AUTHORIZED": 4,
    "SYNTHETIC": 1,
    "UNAUTHORIZED": 1
  },
  "bySeries": {
    "Formula 1": 7,
    "F1TENTH Autonomous Racing": 2,
    "Indy Autonomous Challenge": 1,
    "UA-DETRAC Benchmark": 1,
    "Synthetic Motorsport Simulation": 1
  },
  "bySplit": {
    "BENCHMARK_EVAL": 6,
    "TRAIN": 1,
    "VAL": 1,
    "TEST": 4
  },
  "videos": [...],
  "datasetCardUrl": "/data/cv/DATASET_CARD.md"
}
```

### `GET /api/v1/analysis/cv/evaluation`
Retrieves the comprehensive Computer Vision evaluation suite report, 12-category failure taxonomy breakdown, LOVO / LOEO leakage-free cross-validation folds, and honest `real_world_video_status`.

**Response `200 OK`**:
```json
{
  "realWorldVideoStatus": "INSUFFICIENT_DATA",
  "realVideoStatus": "NOT_AVAILABLE",
  "evaluationStatus": "SYNTHETIC_VALIDATION_ONLY",
  "datasetCatalog": { ... },
  "detectionMetrics": {
    "precision": 1.0,
    "recall": 1.0,
    "f1Score": 1.0,
    "meanIou": 1.0,
    "iouThreshold": 0.50
  },
  "trackingMetrics": { ... },
  "identityMetrics": {
    "evaluationStatus": "INSUFFICIENT_DATA",
    "statement": "Driver identity evaluation requires authoritative camera metadata or helmet/car livery annotations."
  },
  "crossModalMetrics": {
    "evaluationStatus": "NOT_AVAILABLE",
    "spatialAlignmentStatus": "NOT_EVALUATED",
    "discrepancyInterpretation": "DISCREPANCY_IS_EVIDENCE_QUALITY_FLAG_NOT_DRIVER_FAULT"
  },
  "failureCategories": {
    "DETECTION_MISS": 0,
    "FALSE_DETECTION": 0,
    "OCCLUSION": 0,
    "TRUNCATION": 0,
    "TRACK_FRAGMENTATION": 0,
    "ID_SWITCH": 0,
    "IDENTITY_UNAVAILABLE": 0,
    "TIMESTAMP_MISALIGNMENT": 0,
    "CAMERA_GEOMETRY": 0,
    "INSUFFICIENT_RESOLUTION": 0,
    "VIDEO_UNAVAILABLE": 0,
    "OTHER": 0
  },
  "splitsEvaluation": {
    "lovo": { "numFolds": 2, "strategy": "Leave-One-Video-Out", "leakageStatus": "ZERO_LEAKAGE_VERIFIED" },
    "loeo": { "numFolds": 2, "strategy": "Leave-One-Event-Out", "leakageStatus": "ZERO_LEAKAGE_VERIFIED" }
  },
  "stewardNotice": "EVALUATION PURPOSE ONLY: Visual metrics, detections, and tracks are descriptive evidence..."
}
```

### `GET /api/v1/analysis/candidates/{candidate_id}/video/cv`
Retrieves full Computer Vision vehicle detections, multi-object tracks, quality ratings, and identity associations for an incident candidate. Returns `VIDEO_UNAVAILABLE` honestly when broadcast video is commercially restricted or unlinked.

### `GET /api/v1/analysis/candidates/{candidate_id}/video/cv/sufficiency`
Evaluates whether visual evidence is sufficient for human steward review (`SUFFICIENT`, `PARTIALLY_SUFFICIENT`, `INSUFFICIENT`, or `UNAVAILABLE`).
- For commercial cases with unlinked video, returns `steward_readiness: "UNAVAILABLE"` and `VIDEO_EVIDENCE_UNAVAILABLE`.
- Emphasizes that absence of video is unobserved data, never negative evidence or driver guilt.

---

## 11. Explainable Historical Case Intelligence & Side-by-Side Analysis

### `GET /api/v1/evidence/historical/compare/{candidate_id}`
Retrieves observably comparable historical cases based on 7 normalized physical dimensions (corner phase, spatial separation, braking onset, speed relationship, trajectory, apex overlap, exit clearance) with dynamic explainability and side-by-side metric comparison.

**Parameters**:
- `candidate_id` (path, required): Candidate incident ID or benchmark case ID (e.g. `HIST-2024-ITA-R-01`).
- `top_k` (query, optional, default `3`, max `10`): Maximum number of comparable records.
- `circuit` (query, optional): Filter by circuit name (e.g., `Monza`, `Spielberg`).
- `season` (query, optional): Filter by championship season (e.g., `2024`, `2021`).
- `min_similarity` (query, optional, default `0.0`, range `[0.0, 1.0]`): Minimum observable similarity threshold.

**Response `200 OK`**:
```json
{
  "queryCaseId": "HIST-2024-ITA-R-01",
  "comparatorVersion": "historical_comparator_v2",
  "totalCasesEvaluated": 30,
  "comparableCases": [
    {
      "caseId": "HIST-2021-ITA-R-01",
      "series": "Formula 1",
      "season": 2021,
      "event": "Italian Grand Prix",
      "circuit": "Autodromo Nazionale Monza",
      "corner": "Variante del Rettifilo (Turn 1/2)",
      "session": "Race",
      "drivers": ["VER", "HAM"],
      "observableSimilarityScore": 0.825,
      "similarityRank": 1,
      "relevanceGrade": "HIGHLY_COMPARABLE",
      "matchedFeatures": [
        "Late braking onset within 1.5 m of historical case (+10.0 m vs baseline)",
        "Close lateral apex proximity within 0.2 m"
      ],
      "unmatchedFeatures": [
        "Slightly tighter exit clearance (+0.4 m difference)"
      ],
      "dataQuality": "FULL",
      "evidenceAvailability": {
        "telemetry": "AVAILABLE",
        "video": "AVAILABLE",
        "regulation": "AVAILABLE"
      },
      "officialSources": [
        {
          "documentId": "DOC-64",
          "officialDocument": "FIA Stewards Decision — Document 64",
          "sourceUrl": "https://www.fia.com/documents/doc-64",
          "articleNumber": "Article 33.3",
          "documentVersion": "2021 Official Issue",
          "epistemicType": "DOCUMENTARY",
          "provenanceStatus": "CANONICAL_DOCUMENTED"
        }
      ],
      "sideBySide": {
        "currentCaseId": "HIST-2024-ITA-R-01",
        "historicalCaseId": "HIST-2021-ITA-R-01",
        "metrics": [
          {
            "metric": "Interaction Category",
            "currentValue": "FORCING OFF TRACK",
            "historicalValue": "FORCING OFF TRACK",
            "difference": "Identical",
            "uncertainty": "± 0.0 cat",
            "sourceType": "DERIVED",
            "status": "AVAILABLE"
          },
          {
            "metric": "Minimum Lateral Gap",
            "currentValue": "1.5 m ± 0.2 m",
            "historicalValue": "1.4 m ± 0.2 m",
            "difference": "+0.10 m (Wider)",
            "uncertainty": "± 0.2 m",
            "sourceType": "OBSERVED",
            "status": "AVAILABLE"
          }
        ]
      }
    }
  ],
  "nonAdjudicationStatement": "CRITICAL NON-ADJUDICATIVE NOTICE: Historical incident retrieval is based exclusively on observable physical and track geometry features. Historical outcomes do NOT determine current driver guilt, fault, or sporting penalties.",
  "limitations": [
    "Past steward decisions are documentary records and do not constitute binding precedent.",
    "Similarity is derived strictly from observable track geometry, gap, and braking deltas."
  ]
}
```

---

## 12. Steward Case Workspace Endpoints (Prompt 24)

### 12.1 Retrieve Canonical Case Workspace
`GET /api/v1/cases/{candidate_id}/workspace`

Returns the master investigation workspace read model aggregating case metadata, incident summary, stream summaries, triage items, chronological timeline with uncertainties, discrepancies, historical comparables, regulations, and review audit trail.

**Response (200 OK):**
```json
{
  "case": {
    "candidateId": "REF-MONZA-01",
    "incidentId": "INC-001",
    "session": "Italian Grand Prix 2024 — Race",
    "event": "OVERTAKE_APPROACH",
    "circuit": "Monza",
    "timestamp": "13:42:18.4",
    "drivers": ["RIC", "HUL"],
    "incidentStatus": "REQUIRES_REVIEW",
    "reviewStatus": "REQUIRES_REVIEW",
    "analysisVersion": "v1.0"
  },
  "incidentSummary": {
    "incidentType": "OVERTAKE_APPROACH",
    "detectionMethod": "KINEMATIC_RELATIVE_MOTION_ANOMALY",
    "confidence": 85,
    "timelineWindow": "T-2.0s → T+1.5s relative to 13:42:18.4",
    "trackPosition": "Variante del Rettifilo (Turn 1/2)",
    "lapNumber": 1
  },
  "evidenceSummary": {
    "telemetry": {
      "availability": "FULL",
      "epistemicType": "OBSERVED",
      "quality": "High-Fidelity 25Hz Resampled CAN Grid",
      "provenance": "Official FastF1 / OpenF1 Synchronized Timing Feed",
      "timestampCoverage": "T-2.0s → T+1.5s",
      "limitations": ["Interpolated at 25Hz from irregular asynchronous ECU broadcasts"],
      "contradictions": []
    },
    "video": {
      "availability": "UNAVAILABLE",
      "epistemicType": "OBSERVED",
      "quality": "UNAVAILABLE (FOM Copyright)",
      "provenance": "Unlinked Broadcast Stream",
      "timestampCoverage": "0.0s",
      "limitations": [
        "Commercial broadcast footage is legally protected under copyright and cannot be redistributed.",
        "Unlinked video frames are recorded as unobserved data, never as negative evidence or proof of guilt."
      ],
      "contradictions": []
    }
  },
  "evidenceItems": [
    {
      "evidenceId": "EV-REF-MONZA-01-TEL-RAW",
      "evidenceType": "TELEMETRY",
      "epistemicType": "OBSERVED",
      "source": "FastF1 / OpenF1 25Hz Resampled SI Grid",
      "availability": "FULL",
      "quality": "Quality Score 85/100",
      "timestamp": "13:42:18.4",
      "relevance": "Relevant to telemetry",
      "provenance": "FastF1 Official Timing & Telemetry Feed",
      "limitations": ["Interpolated at 25Hz from irregular asynchronous ECU broadcasts"],
      "discrepancyStatus": "NONE",
      "observation": "Raw 25Hz Cartesian Coordinates and ECU Sensor Channels",
      "parentEvidenceIds": [],
      "triagePriority": 1,
      "latestAcknowledgement": null
    }
  ],
  "timeline": [
    {
      "timestamp": "13:42:16.4",
      "eventRelativeTimeSec": -2.0,
      "source": "FastF1 Telemetry",
      "epistemicType": "OBSERVED",
      "description": "Initial Approach Established",
      "measurement": "Velocity 332.4 km/h",
      "uncertainty": "± 2.0 km/h (ECU CAN bus sample accuracy)",
      "provenance": "FastF1 Telemetry Log"
    }
  ],
  "discrepancies": [
    {
      "discrepancyId": "DISC-TEL-VID-01",
      "evidenceA": "FastF1 Telemetry",
      "evidenceB": "Broadcast Video",
      "discrepancyType": "Timestamp Calibration Offset",
      "magnitude": "0.28 s",
      "uncertainty": "± 0.04 s",
      "explanation": "Telemetry peak deceleration precedes visual contact point by 7 video frames.",
      "severity": "LOW",
      "status": "OPEN",
      "affectedEvidenceIds": ["EV-TEL-RAW"],
      "notes": []
    }
  ],
  "doctrine": "CRITICAL STEWARD DOCTRINE: This workspace organizes empirical, kinematic, and documentary evidence to assist human race stewards. It strictly DOES NOT automate driver guilt, assign fault probabilities, issue penalties, or make legal adjudications. Human stewards retain exclusive decision authority."
}
```

### 12.2 Record Reviewer Evidence Acknowledgement
`POST /api/v1/cases/{candidate_id}/evidence/{evidence_id}/review`

**Request Body:**
```json
{
  "reviewerId": "steward-1",
  "action": "CONSIDERED",
  "note": "Verified ECU brake trace against baseline."
}
```

### 12.3 Open / Update Unresolved Investigation Question
`POST /api/v1/cases/{candidate_id}/questions`
```json
{
  "question": "Camera coverage does not establish rear-wheel overlap at apex.",
  "evidenceIds": ["EV-TEL-RAW", "EV-CV-TRACK-01"],
  "reviewerNote": "Request secondary trackside camera timecode alignment."
}
```

`PATCH /api/v1/cases/{candidate_id}/questions/{question_id}`
```json
{
  "status": "RESOLVED",
  "reviewerNote": "Lateral telemetry displacement confirms 60% overlap maintained throughout apex phase."
}
```

### 12.4 Update Discrepancy Status
`POST /api/v1/cases/{candidate_id}/discrepancies/{discrepancy_id}/status`
```json
{
  "status": "ACKNOWLEDGED",
  "reviewerId": "steward-panel",
  "note": "Acknowledged 0.28s temporal offset; telemetry prioritized for velocity profile."
}
```


