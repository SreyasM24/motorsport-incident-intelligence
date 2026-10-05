# PROMPT 25 INTEGRATION AUDIT: ARCHITECTURAL SUBSYSTEM REVIEW
**Motorsport Incident Intelligence (MII)**
*Date: 2026-10-01 | Branch: main*

---

## 1. Executive Summary & Objective

The objective of Prompt 25 is to validate that the complete Motorsport Incident Intelligence platform functions as **one cohesive, deterministic, evidence-first system** for race stewards and officiating bodies. Prior prompts (Prompts 1 through 24) established individual subsystems: ingestion, kinematic reconstruction, multi-modal synthesis, regulation retrieval, historical case comparison, and the steward case investigation workspace.

This audit inspects every subsystem boundary, data transition, persistence contract, caching layer, and failure boundary across the entire stack.

---

## 2. End-to-End Data Flow

```text
REAL SESSION DATA (FastF1 / OpenF1)
       ↓ [Raw Telemetry: Speed, RPM, Throttle, Brake, Gear, DRS, 3D Coordinates]
INGESTION HUB (`app/services/ingestion_service.py`)
       ↓ [Normalized 25Hz Resampled CAN Grid]
TELEMETRY & KINEMATICS PREPROCESSING (`app/services/telemetry_service.py`, `app/physics/`)
       ↓ [Pairwise Kinematics, Proximity, Relative Velocity, Braking Point Deltas]
INCIDENT CANDIDATE DETECTION (`app/evidence/detector.py`, `app/evidence/segmenter.py`)
       ↓ [CandidateDossier, Episode Temporal Windows, Peak Timestamps]
INCIDENT RECONSTRUCTION (`app/evidence/reconstruction_service.py`, `app/services/overtake_geometry_service.py`)
       ↓ [IncidentEvidenceDossier, Spatial Trajectories, Axle Overlap %]
REGULATION KNOWLEDGE RETRIEVAL (`app/knowledge/retriever.py`, `app/knowledge/service.py`)
       ↓ [BM25/Semantic Hybrid Citations, Official Articles, Source Conflict Detection]
HISTORICAL COMPARABLE-CASE INTELLIGENCE (`app/benchmark/comparator.py`, `app/benchmark/service.py`)
       ↓ [Physical Kinematic Matching across 30 Verified Historical Cases, Isolated Precedents]
VIDEO / CV EVIDENCE (`app/evidence/cv/`, `app/evidence/visual/`)
       ↓ [Visual Bounding Boxes, Overlap Tracking, or Explicit UNAVAILABLE Status]
MULTI-MODAL EVIDENCE SYNTHESIS (`app/evidence/synthesis/synthesizer.py`)
       ↓ [StewardEvidenceDossier: Unified Epistemic Typing, Cross-Modal Discrepancies]
PERSISTENCE SERVICE (`app/services/candidate_persistence_service.py`)
       ↓ [PostgreSQL / SQLite: Race, Session, Driver, Incident, IncidentDriver, ReviewRecord]
STEWARD CASE WORKSPACE (`app/services/workspace_service.py`)
       ↓ [StewardCaseWorkspace: Deterministic Triage, Timeline ± Uncertainties, Review Summary]
HUMAN REVIEW & TRIAGE (`app/api/workspace.py`, `app/api/incidents.py`, Frontend UI)
       ↓ [Granular Stream Acknowledgements, Unresolved Questions, Discrepancy Annotations]
IMMUTABLE AUDIT TRAIL (`ReviewRecord`, `EvidenceAcknowledgement`, `DiscrepancyAnnotation`)
```

---

## 3. Subsystem Boundaries & Data Contracts

| Subsystem | Input Object | Output Object | Persisted? | Recomputed? | Cached? |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Ingestion** | Session/Round/Driver params | `RawTelemetry`, `List[TelemetryPointSchema]` | No | On demand | Disk (FastF1) + In-Memory |
| **Telemetry / Kinematics** | Raw streams from 2 drivers | `List[SynchronizedFrame]`, `PairwiseFeatures` | No | On demand | No |
| **Baseline Modeling** | Driver session telemetry | `ReferenceLapProfile`, delta metrics | No | On demand | In-Memory (service level) |
| **Candidate Detection** | Synchronized frames + features | `List[CandidateDossier]` | Yes (upon persist) | On demand | In-Memory (`_candidate_cache`) |
| **Incident Reconstruction** | Candidate + track geometry | `IncidentEvidenceDossier` | No | On demand | In-Memory |
| **Regulation Retrieval** | Event type + telemetry query | `RegulationEvidenceSummary`, `List[RegulatoryCitation]` | Static catalog | On query | Static in-memory inverted index |
| **Historical Comparator** | Incident physical metrics | `HistoricalComparisonResult`, `List[HistoricalComparableIncident]` | Static benchmark | On query | Static benchmark manifest |
| **CV / Visual Tracking** | Video timestamps + bounding boxes | `CVIncidentAnalysis`, `VisualEvidencePackage` | No | On demand | Explicit `UNAVAILABLE` fallback |
| **Multi-Modal Synthesis** | Candidate + CV + Regs + RC | `StewardEvidenceDossier` | No | On demand | In-Memory (`_DOSSIER_CACHE`) |
| **Candidate Persistence** | `CandidateDossier` | `Incident`, `ReviewRecord`, `IncidentDriver` | Yes (DB) | Idempotent | N/A |
| **Steward Workspace** | `candidate_id` + DB session | `StewardCaseWorkspace` | Yes (mutations) | On demand | In-Memory (300s TTL) |
| **Human Review** | Steward review form / notes | `ReviewRecord` | Yes (DB) | Append-only | N/A |
| **Evidence Acknowledgement** | `EvidenceAcknowledgementCreateRequest` | `EvidenceAcknowledgement` | Yes (DB) | Append-only | N/A |
| **Unresolved Questions** | `UnresolvedQuestionCreateRequest` | `UnresolvedQuestion` | Yes (DB) | Mutable status | N/A |
| **Discrepancy Lifecycle** | `DiscrepancyStatusUpdateRequest` | `DiscrepancyAnnotation` | Yes (DB) | Append-only audit | N/A |
| **Conversational Assistant**| Natural language question + case ID | `AssistantQueryResponse` | No | On query | Grounded in workspace |

---

## 4. Deep-Dive Subsystem Audit

### A. Data Ingestion & Preprocessing
- **Source**: FastF1 public API / OpenF1 REST API.
- **Normalization**: Resamples asynchronous CAN bus telemetry onto a uniform 25Hz grid ($\Delta t = 40\text{ms}$).
- **Boundary Validation**: Physical sanity checks verify velocities ($0 \le v \le 380\text{ km/h}$), accelerations ($|a_{\text{long}}| \le 6.5\text{G}$, $|a_{\text{lat}}| \le 6.5\text{G}$), and steering angles.
- **Degraded Behavior**: Missing telemetry raises `DataUnavailableException` or returns empty frames with `INSUFFICIENT_DATA`. It never interpolates across gaps $> 1.0\text{s}$ or fabricates sensor readings.

### B. Incident Reconstruction & Overtake Geometry
- **Spatial Modeling**: Reconstructs 2D coordinate paths $(X, Y)$ relative to the track centerline and corner apex.
- **Kinematic Metrics**: Computes minimum lateral clearance ($\Delta_{\text{Apex}}$), axle overlap percentage at Entry, Apex, and Exit, time-to-collision ($\text{TTC}$), and deceleration delta ($\Delta a_{\text{long}}$).
- **Epistemic Classification**:
  - Direct telemetry $\to$ `OBSERVED`
  - Geometric derivations (overlap %, apex distance) $\to$ `DERIVED`
  - Braking delta vs. baseline $\to$ `MODEL_DERIVED`
- **Lineage**: Every metric contains source sensor names, sampling rate, and timestamp offsets.

### C. Regulation Knowledge Layer (Prompt 21 RAG)
- **Repository**: Canonical repository of FIA Formula One Sporting Regulations (2023 & 2024), ISC Appendix L Chapter IV, and Driving Standards Guidelines.
- **Retrieval Engine**: BM25 lexical search, semantic n-gram matching, and hybrid weighted reranking.
- **Epistemic Classification**: `DOCUMENTARY`.
- **Integrity**: Grounded citations with full article numbers, exact statutory excerpts, and source URLs. Discrepancy detector flags `SOURCE_CONFLICT` if season rules diverge. Never provides a legal ruling or penalty recommendation.

### D. Historical Comparable-Case Intelligence (Prompt 23)
- **Dataset**: 30 verified historical incidents across 8 circuits (Monza, Red Bull Ring, COTA, Mexico, Spa, Silverstone, Interlagos, Las Vegas) and 2 seasons (2023–2024), plus 12 nominal controls.
- **Comparator**: Normalizes 7 physical dimensions (axle overlap %, lateral clearance, entry speed, braking delta, turn type, wet/dry surface, track limits).
- **Precedent Isolation**: Driver identity, team identity, and past documentary steward penalties are strictly isolated from similarity scoring. Past penalties are provided purely as historical documentary context.

### E. Video & CV Foundation (Prompt 22)
- **Broadcast Footage Availability**: FOM broadcast footage is copyrighted and not distributed in the repository.
- **Real-World Video Evaluation State**: Explicitly marked `INSUFFICIENT_DATA` / `UNAVAILABLE`.
- **Integrity Guardrail**: Synthetic or mock bounding boxes are never passed off as real Formula 1 footage. Dual-coordinate contracts ensure pixel coordinates $(u, v)$ and spatial coordinates $(X, Y)$ remain distinct.

### F. Multi-Modal Synthesis & Discrepancies
- **Dossier Synthesizer**: Unifies telemetry, race control messages, regulatory context, and visual streams into a cohesive `StewardEvidenceDossier`.
- **Cross-Modal Discrepancy Engine**: Automatically evaluates cross-stream consistency:
  - Visual contact claimed vs. IMU acceleration spike absence.
  - Driver steering input divergence vs. car trajectory yaw rate.
  - Driver throttle lift claims vs. CAN bus throttle percentage.
- **Epistemic Guardrail**: Discrepancies are flagged as `OPEN`; the system never automatically reconciles or resolves them.

### G. Candidate Persistence & Human Review State Machine
- **Identity & Idempotency**:
  - Deterministic candidate fingerprint: `hash(session_id + drv_a + drv_b + lap + start_time + end_time)`.
  - Re-ingesting or re-persisting the same candidate does not create duplicate database rows.
- **State Machine**:
  - `REQUIRES_REVIEW` $\to$ `UNDER_REVIEW`
  - `UNDER_REVIEW` $\to$ `REVIEWED` (requires reviewer notes)
  - `UNDER_REVIEW` $\to$ `DISMISSED` (requires rationale)
  - `UNDER_REVIEW` $\to$ `REQUIRES_REVIEW` (paused)
  - Terminal states (`REVIEWED`, `DISMISSED`) cannot transition to each other.
  - Reopening from terminal states to `UNDER_REVIEW` strictly requires an explicit, non-empty `reopen_reason`.
- **Audit Logging**: Every state transition generates an immutable `ReviewRecord` row recording reviewer, timestamp, and notes.

### H. Steward Case Investigation Workspace (Prompt 24)
- **Composite Payload**: Single canonical REST response (`/cases/{candidate_id}/workspace`) consumed by the frontend.
- **Deterministic Triage**:
  - Priority 1: Direct kinematics & physical sensor readings (`OBSERVED`).
  - Priority 2: Spatial trajectory & reference overlays (`DERIVED` / `MODEL_DERIVED`).
  - Priority 3: Regulatory context & relevant statutory articles (`DOCUMENTARY`).
  - Priority 4: Interaction pattern classification (`MODEL_DERIVED`).
  - Priority 5: Visual detection & camera context (`OBSERVED` / `UNAVAILABLE`).
- **Timeline with Uncertainty Bounds**:
  - Lateral position: $\pm 0.20\text{ m}$
  - Relative velocity: $\pm 2.0\text{ km/h}$
  - Temporal synchronization: $\pm 0.04\text{ s}$ ($\pm 1$ frame at 25Hz)
- **Reviewer Mutations**:
  - Granular acknowledgements (`CONSIDERED`, `NOT_RELEVANT`, `INSUFFICIENT`, `CONTRADICTORY`, `REQUIRES_FOLLOW_UP`) preserve source evidence immutability.
  - Unresolved question tracking with linked evidence tags.
  - Discrepancy status annotations (`OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `UNRESOLVED`).

### I. Conversational Assistant
- Grounded strictly in the active case workspace.
- Adjudicative refusal guardrail: Direct or indirect queries asking for guilt, fault, liability, or penalty recommendations are unequivocally refused with standard non-adjudication doctrine.

---

## 5. Persistence vs. Recomputation vs. Caching Matrix

| Artifact | Persistence Store | Recomputed? | Caching Mechanism |
| :--- | :--- | :--- | :--- |
| **Race & Session Info** | PostgreSQL `races`, `sessions` | On ingestion | In-Memory DB session |
| **Driver Records** | PostgreSQL `drivers` | On ingestion | In-Memory DB session |
| **Telemetry Points** | PostgreSQL `telemetry_points` | On ingestion | FastF1 disk cache |
| **Incident Candidate** | PostgreSQL `incidents` | On persistence | `_candidate_cache` (RAM) |
| **Incident-Driver Links** | PostgreSQL `incident_drivers` | On persistence | In-Memory DB session |
| **Review Records** | PostgreSQL `reviews` | Append-only on review | In-Memory DB session |
| **Evidence Acknowledgement**| PostgreSQL `evidence_acknowledgements` | Append-only on triage | In-Memory DB session |
| **Unresolved Questions** | PostgreSQL `unresolved_questions` | Mutable on question action| In-Memory DB session |
| **Discrepancy Annotation** | PostgreSQL `discrepancy_annotations` | Append-only on transition| In-Memory DB session |
| **Evidence Dossier** | Generated in memory | On demand / candidate ID | `_DOSSIER_CACHE` (300s TTL) |
| **Workspace Payload** | Composite serialization | Assembled on request | Warm cache: 0.15ms latency |
| **Historical Benchmark** | `app/benchmark/manifest.py` | Evaluated on demand | Static in-memory dictionary |
| **Regulation Citations** | `app/knowledge/repository.py` | Queried on demand | In-memory inverted index |

---

## 6. Duplications, Mocks, and Limitations Audit

### A. Calculations & Contracts
- **Clean Contracts**: CamelCase JSON contracts are enforced uniformly across schemas via Pydantic `alias_generator = to_camel` and `populate_by_name = True`.
- **Single Source of Truth**: Backend is the authoritative source for all physical, spatial, and regulatory calculations. The React frontend strictly renders backend payloads and never re-implements physics or geometry algorithms.

### B. Mock / Synthetic Components
- **Video Feeds**: Broadcast video is absent due to commercial licensing. Video streams are honestly categorized as `UNAVAILABLE` or `INSUFFICIENT_DATA`. Synthetic test frames exist only in unit tests and are never served as production evidence.
- **FastF1 Offline Fallbacks**: The test suite uses pre-recorded telemetry fixtures to enable isolated, reproducible testing without internet dependencies.

### C. Known Limitations
1. **GPS Spatial Accuracy**: F1 car GPS coordinates have standard civilian jitter of $\pm 0.5\text{m}$ to $\pm 1.0\text{m}$, which is smoothed via spline interpolation and bounded by track limits.
2. **Asynchronous Sensor Sampling**: CAN bus telemetry items arrive at differing frequencies (10Hz–100Hz) and are resampled to 25Hz with a $\pm 0.04\text{s}$ uncertainty envelope.
3. **Steward Precedent Independence**: Historical documentary outcomes are provided purely as comparative reference context. The system prevents treating historical steward decisions as binding precedent or physical truth.

---

## 7. Audit Conclusion & Prompt 25 Plan of Action

The architectural subsystems are cleanly decoupled and adhere to the project's epistemic integrity principles. The next steps for Prompt 25 are:
1. Construct the deterministic end-to-end case replay harness (`CaseReplayHarness`).
2. Implement comprehensive integration tests in `backend/app/tests/test_end_to_end_case_replay.py` covering determinism, idempotency, failure modes, transaction integrity, evidence immutability, state machine enforcement, assistant grounding, and cross-circuit execution.
3. Measure performance profiles across cold vs. warm replays.
4. Validate live against Monza reference cases (`REF-MONZA-01`, `02`, `03`) and Austrian GP benchmark cases (`HIST-2024-AUT-01`).
5. Update repository documentation (`docs/end-to-end-validation.md`, `docs/evaluation.md`, `docs/api.md`, `docs/steward-workflow.md`, `README.md`).
6. Execute full test regression and push to GitHub.
