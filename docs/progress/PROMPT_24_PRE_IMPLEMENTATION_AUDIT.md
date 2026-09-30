# PROMPT 24 PRE-IMPLEMENTATION AUDIT: STEWARD INVESTIGATION WORKFLOW, EVIDENCE TRIAGE & DECISION-READY CASE REVIEW

**Date:** 2026-09-30  
**Repository:** [Motorsport Incident Intelligence](https://github.com/SreyasM24/motorsport-incident-intelligence.git)  
**Baseline Commit:** `e6252a0` (*feat: add explainable historical comparable-case intelligence*)  
**Scope:** Architectural and state audit across Prompts 07, 16, 17, 20, 21, 22, and 23 before implementing Prompt 24.

---

## 1. Executive Summary

This pre-implementation audit examines existing subsystems across the backend and frontend to ensure Prompt 24 builds cleanly on top of prior foundations without duplicating contracts, inventing competing DTOs, or weakening core epistemic and non-adjudicative guardrails.

The objective of Prompt 24 is to provide a unified, evidence-first **Steward Case Workspace** that enables human race stewards to systematically triage evidence streams, examine chronologically ordered incident timelines with explicit uncertainties, identify and manage cross-modal discrepancies, record evidence acknowledgements, track unresolved investigation questions, and preserve an immutable audit trail.

---

## 2. Deep-Dive Audit of Existing Implementations

### 2.1 Existing Candidate States & Lifecycle State Machine
- **Location:** `backend/app/schemas/review.py`, `backend/app/models/incident.py`, `backend/app/services/candidate_persistence_service.py`
- **Enum `ReviewStatus`:**
  - `REQUIRES_REVIEW`: Initial state of an algorithmically flagged candidate.
  - `UNDER_REVIEW`: Steward has opened formal evaluation.
  - `REVIEWED`: Closed with human steward rationale and regulatory references.
  - `DISMISSED`: Closed without formal sporting sanction.
- **Allowed Transitions:**
  - `REQUIRES_REVIEW -> UNDER_REVIEW`
  - `UNDER_REVIEW -> REVIEWED | DISMISSED | REQUIRES_REVIEW`
  - `REVIEWED -> UNDER_REVIEW` (Enforces mandatory non-empty `reopen_reason`)
  - `DISMISSED -> UNDER_REVIEW` (Enforces mandatory non-empty `reopen_reason`)
  - Legacy `DETECTED -> REQUIRES_REVIEW | UNDER_REVIEW`
- **Assessment:** Rock-solid state machine with strict transition guards and reopening audit rationale. Fully reusable.

### 2.2 Existing Review Records & Persistence
- **Location:** `backend/app/models/review.py` (`ReviewRecord`), `backend/app/schemas/review.py` (`ReviewRecordSchema`, `ReviewCreateRequest`)
- **Fields:** `id`, `incident_id`, `status`, `reviewer_id`, `review_started_at`, `review_completed_at`, `evidence_considered`, `evidence_missing`, `observations`, `review_notes`, `review_rationale`, `regulatory_references`, timestamps.
- **Assessment:** Records human steward evaluation; completely free of automated AI guilt or penalties. We will extend review support with granular reviewer evidence acknowledgements and unresolved question tracking.

### 2.3 Existing Dossier Structures & Synthesis Layer
- **Location:** `backend/app/evidence/synthesis/contracts.py`, `backend/app/evidence/synthesis/synthesizer.py`
- **Contracts:**
  - `StewardEvidenceDossier`: Master dossier aggregating timeline, evidence items, stream quality, consistency, consensus, discrepancies, regulations, historical comparables, limitations, and steward doctrine.
  - `EvidenceItem`: Individual observation/derivation with `evidence_id`, `evidence_type`, `status` (`EvidenceStatus`), `measurement_basis`, `provenance`, `limitations`, `parent_evidence_ids`.
  - `EvidenceQualityRecord`: Stream availability (`AVAILABLE`, `PARTIAL`, `UNAVAILABLE`), temporal/spatial validity, measurement uncertainty, missingness notes.
  - `DossierExportPayload`: Deterministic export wrapper for FIA external compliance.
- **Assessment:** Canonical master dossier contract is already discrepancy-aware and multi-modal. Fully reusable as the core data provider for the workspace.

### 2.4 Existing Evidence Types & Epistemic Taxonomy
- **Location:** `backend/app/evidence/synthesis/contracts.py`
- **`EvidenceType`:** `TELEMETRY`, `REFERENCE_BASELINE`, `OVERTAKE_GEOMETRY`, `ML_INTERACTION`, `VIDEO_SYNCHRONIZATION`, `VISUAL`, `COMPUTER_VISION`, `REGULATION`.
- **`EvidenceStatus` (Epistemic Categories):**
  - `OBSERVED`: Direct sensor/physical measurement (raw ECU CAN-bus, raw video timecode).
  - `DERIVED`: Deterministic mathematical transformation (closing rate, minimum gap, apex overlap).
  - `MODEL_DERIVED`: Hypothesis emitted by statistical or ML/CV model (bounding box track, ML anomaly probability).
  - `DOCUMENTARY`: Official regulatory or race control documentary reference.
  - `UNAVAILABLE`: Unobserved, unlinked, or commercially restricted stream.
- **Assessment:** Meets Prompt 24 requirements exactly. No changes to the taxonomy required.

### 2.5 Existing Provenance, Lineage & Anti-Double-Counting
- **Location:** `backend/app/evidence/synthesis/lineage.py` (`LineageTracker`), `backend/app/evidence/synthesis/contracts.py`
- **Features:** Traces parent evidence IDs, roots, and computational derivations. Computes `independent_observation_count` in `EvidenceConsensus` to prevent treating derived metrics as separate empirical observations.
- **Assessment:** Strict compliance with Prompt 16 and Prompt 20 lineage guidelines. Reused directly.

### 2.6 Existing Discrepancy Model
- **Location:** `backend/app/evidence/synthesis/contracts.py` (`CrossModalDiscrepancy`, `DiscrepancySeverity`, `ConsistencyStatus`), `backend/app/evidence/synthesis/consistency.py` (`ConsistencyEngine`)
- **Fields:** `discrepancy_id`, `evidence_stream_a`, `evidence_stream_b`, `metric`, `observed_difference`, `expected_tolerance`, `severity`, `status` (defaults to `"OPEN"`), `explanation`, `provenance`, `affected_evidence_ids`.
- **Assessment:** Prompt 24 requires extending this model to support lifecycle statuses (`OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `UNRESOLVED`) and human steward status updates without auto-resolving contradictions.

### 2.7 Existing Historical Comparable Cases
- **Location:** `backend/app/benchmark/comparator.py`, `backend/app/knowledge/historical_retriever.py`, `backend/app/api/evidence.py`
- **Features:** Prompt 23 explainable comparable cases with 7 physical dimensions, missing data renormalization, zero precedent distortion ($\Delta = 0.000000$), zero driver/team bias ($\Delta = 0.000000$), matched/unmatched explainability bullets, side-by-side metric comparison with sensor uncertainty bounds ($\pm 0.2\text{ m}$, etc.).
- **Assessment:** Complete and fully verified. Reused directly in the workspace read model.

### 2.8 Existing Regulation Retrieval
- **Location:** `backend/app/knowledge/service.py`, `backend/app/knowledge/retriever.py`, `backend/app/api/evidence.py`
- **Features:** Prompt 21 citation-grounded hybrid retrieval (BM25 + N-gram semantic), temporal validity checking, source conflict detection.
- **Assessment:** Complete and verified. Reused directly.

### 2.9 Existing Assistant Behavior
- **Location:** `backend/app/api/assistant.py`
- **Features:** Handles queries on telemetry anomalies, regulations, missing evidence, video unavailability reasons, and historical comparable cases with mandatory non-adjudication banners.
- **Assessment:** Needs extension to ground queries in active case workspace state (e.g., active discrepancies, triage counts, unresolved questions).

### 2.10 Existing Frontend Incident Detail Workflow
- **Location:** `frontend/src/views/IncidentDetailView.tsx`
- **Sections:**
  - Header with status badges and candidate meta
  - Section 2: Video Evidence (with Honest FOM copyright caveats)
  - Section 3: Incident Timeline
  - Section 4: Telemetry Evidence (25Hz FastF1 charts)
  - Section 4B: Reference-Lap Baseline
  - Section 4C: Overtake Geometry
  - Section 4D: ML Evidence
  - Section 4E: Master Steward Evidence Dossier & Discrepancies
  - Section 4F: Historical Comparable Panel (Prompt 23)
  - Section 5: Evidence Assessment
  - Section 6: Relevant Regulations & Flow
  - Section 7: Uncertainty & Caveats
  - Section 8: Embedded AI Assistant
  - Section 9: Steward Review Form & Audit Records
- **Assessment:** Highly rich but currently presented as a long monolithic scroll. Needs enhancement into a structured, tabbed/filtered investigation workspace with dedicated Evidence Triage, Discrepancy Management, Unresolved Questions, and Reviewer Acknowledgements.

### 2.11 Existing APIs
- `GET /api/v1/incidents` & `GET /api/v1/incidents/{id}`
- `GET /api/v1/analysis/candidates/{candidate_id}/steward-dossier`
- `GET /api/v1/analysis/candidates/{candidate_id}/steward-dossier/export/json`
- `POST /api/v1/analysis/candidates/persist` & `persist-batch`
- `POST /api/v1/incidents/{id}/reviews` & `GET /api/v1/incidents/{id}/reviews`
- `GET /api/v1/evidence/historical/compare/{candidate_id}`
- `GET /api/v1/evidence/regulations/search`
- `POST /api/v1/assistant/query`

---

## 3. Explicit Gap Analysis: What is Missing?

1. **Canonical Case Workspace Read Model (`StewardCaseWorkspace`):**
   - No single endpoint returns a unified case workspace aggregating case metadata, incident summary, evidence stream triage, ordered timeline, active discrepancies, unresolved questions, reviewer acknowledgements, and review audit history.
2. **Deterministic Evidence Triage & Prioritization:**
   - Evidence items are generated in the dossier, but there is no explicit triage layer categorizing them by epistemic status (`OBSERVED`, `DERIVED`, `MODEL_DERIVED`, `DOCUMENTARY`, `UNAVAILABLE`) and availability (`FULL`, `PARTIAL`, `LIMITED`, `UNAVAILABLE`) with deterministic UX ordering (observed -> derived -> model-derived -> documentary -> unavailable).
3. **Structured Reviewer Evidence Acknowledgements:**
   - Stewards currently select coarse checkboxes in the review form (`evidenceConsidered`), but cannot mark individual evidence items with specific inspection actions (`CONSIDERED`, `NOT_RELEVANT`, `INSUFFICIENT`, `CONTRADICTORY`, `REQUIRES_FOLLOW_UP`) with notes and timestamps.
4. **Structured Unresolved Questions Mechanism:**
   - No structured table/schema exists for human stewards to log open technical questions (e.g. *"Camera coverage does not establish rear-wheel overlap"*), track their status (`OPEN`, `RESOLVED`, `DEFERRED`), and associate them with affected evidence IDs.
5. **Discrepancy Investigation Status Workflow:**
   - Discrepancies in the dossier have status `"OPEN"`, but there is no mechanism for a steward to acknowledge, document, or transition their status (`OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `UNRESOLVED`).
6. **Workspace REST Endpoints:**
   - Missing canonical `GET /api/v1/cases/{candidate_id}/workspace`
   - Missing `POST /api/v1/cases/{candidate_id}/evidence/{evidence_id}/review`
   - Missing `POST /api/v1/cases/{candidate_id}/questions`
   - Missing `PATCH /api/v1/cases/{candidate_id}/questions/{question_id}`
   - Missing `GET /api/v1/cases/{candidate_id}/timeline`
   - Missing `GET /api/v1/cases/{candidate_id}/audit`

---

## 4. Architectural Reuse Plan

| Component | Status | Strategy in Prompt 24 |
|---|---|---|
| `ReviewStatus` state machine | **REUSE** | Keep existing state machine and transition validator (`validate_status_transition`). |
| `ReviewRecord` database model | **EXTEND** | Add JSON/relationship support for reviewer acknowledgements and unresolved questions, or dedicated child models with foreign keys to preserve immutability. |
| `StewardEvidenceDossier` | **REUSE** | Serve as the multi-modal evidence generator powering the workspace read model. |
| `EvidenceStatus` & `EvidenceType` | **REUSE** | Standard epistemic taxonomy (`OBSERVED`, `DERIVED`, `MODEL_DERIVED`, `DOCUMENTARY`, `UNAVAILABLE`). |
| `HistoricalCaseComparator` (Prompt 23) | **REUSE** | Integrate `HistoricalComparisonResponse` directly into `historical_comparables` of workspace. |
| `KnowledgeRetrievalService` (Prompt 21) | **REUSE** | Integrate citation-grounded regulations directly into `regulations` of workspace. |
| `LineageTracker` (Prompt 16) | **REUSE** | Keep provenance parent tracking across all evidence items. |
| `IncidentDetailView.tsx` | **EXTEND** | Refactor into dedicated tabs/sections: Case Header, Incident Timeline, Evidence Triage, Discrepancies, Historical Comparables, Regulations, Reviewer Notes, Unresolved Questions, Audit History. |
| `Assistant` (Prompt 21/23) | **EXTEND** | Ground responses in case workspace evidence streams, active discrepancies, and unresolved questions. |

---

## 5. What Will NOT Be Changed

1. **NO Automated Penalty Recommendations:** The system will never compute penalties or suggest sporting punishments.
2. **NO Guilt / Fault Probabilities:** No algorithmic allocation of driver liability or blame.
3. **NO Modification of Raw/Source Evidence:** Reviewer metadata, acknowledgements, and notes will be stored in isolated review tables; raw telemetry, video timecodes, and reference baselines remain strictly immutable.
4. **NO Conversion of Missing Data to Zero:** Missing video or telemetry remains explicitly `UNAVAILABLE` or `LIMITED`.
5. **NO Precedent Distortion in Similarity:** Past steward verdicts remain excluded from mathematical case comparison.
6. **NO Driver Identity / Reputation Biases:** Driver names, teams, and standings have 0 weight in physical evidence.

---

## 6. Target Architecture for Prompt 24

```
                                      +---------------------------------------------+
                                      |            Human Steward Panel              |
                                      +---------------------------------------------+
                                                            |
                                               Interactive Investigation
                                                            v
+-------------------------------------------------------------------------------------------------------------------+
|                                            STEWARD CASE WORKSPACE                                                 |
|                                                                                                                   |
|  +--------------------+   +-----------------------+   +-----------------------+   +----------------------------+  |
|  |    Case Header     |   |   Incident Timeline   |   |    Evidence Triage    |   | Cross-Modal Discrepancies  |  |
|  | - Status Badge     |   | - Chronological T-2s  |   | - OBSERVED            |   | - Telemetry vs Video       |  |
|  | - Session / Drivers|   | - Uncertainty Bounds  |   | - DERIVED             |   | - RC vs Telemetry          |  |
|  | - Lap / Corner     |   | - Provenance Anchors  |   | - MODEL_DERIVED       |   | - Status: OPEN/ACK/RES     |  |
|  +--------------------+   +-----------------------+   | - DOCUMENTARY         |   +----------------------------+  |
|                                                       | - UNAVAILABLE         |                                   |
|  +--------------------+   +-----------------------+   +-----------------------+   +----------------------------+  |
|  | Hist. Comparables  |   |  Ground Regulations   |                               |   Unresolved Questions     |  |
|  | (Prompt 23 Engine) |   |  (Prompt 21 RAG)      |   +-----------------------+   | - Open / Deferred / Res    |  |
|  | - Side-by-Side     |   | - Citation Grounded   |   | Reviewer Evidence Ack |   | - Linked Evidence IDs      |  |
|  | - Zero Precedent   |   | - Source Conflicts    |   | - CONSIDERED/INSUFF   |   +----------------------------+  |
|  +--------------------+   +-----------------------+   | - Non-Mutating Audit  |                                   |
|                                                       +-----------------------+   +----------------------------+  |
|  +------------------------------------------------+                               |    Immutable Audit Trail   |  |
|  |             AI Steward Assistant               |                               | - Who, When, What, Why     |  |
|  | Grounded in Workspace • Refuses Guilt / Verdict|                               +----------------------------+  |
|  +------------------------------------------------+                                                               |
+-------------------------------------------------------------------------------------------------------------------+
                                                            |
                                        Backed by Canonical Persistence & Dossier
                                                            v
                                  [FastF1 25Hz / DB SQLite/PostgreSQL / Manifest]
```

---

## 7. Next Steps in Execution Order

1. **Data Models & Schema (`backend/app/models/`, `backend/app/schemas/`):**
   - Create models and schemas for `EvidenceAcknowledgement` and `UnresolvedQuestion`.
   - Update `ReviewRecord` and create `StewardCaseWorkspace` canonical read model.
2. **Workspace Service & Deterministic Evidence Triage (`backend/app/services/workspace_service.py`):**
   - Build triage aggregator with deterministic UX ordering and timeline builder.
   - Discrepancy management with status transitions.
3. **Workspace API Endpoints (`backend/app/api/workspace.py`):**
   - Expose `/api/v1/cases/{candidate_id}/workspace` and supporting endpoints.
4. **AI Assistant Integration (`backend/app/api/assistant.py`):**
   - Ground case queries in workspace state.
5. **Frontend Workspace (`frontend/src/views/IncidentDetailView.tsx`, new components):**
   - Implement Case Header, Evidence Triage tabs, Timeline, Discrepancies, Questions, Acknowledgements, Audit Trail.
6. **Comprehensive Automated Tests (`backend/app/tests/test_steward_workspace.py`):**
   - Test all 17 categories + critical safety tests (A-G).
7. **Verification & Push:**
   - Full regression suite, frontend build, docker config, push to origin main.
