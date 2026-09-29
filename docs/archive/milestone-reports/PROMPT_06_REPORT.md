# PROMPT 06 — MULTI-MODAL EVIDENCE FUSION & INCIDENT DOSSIER REPORT
**Project:** Motorsport Incident Intelligence (MII)  
**System:** AI-Assisted Steward Evidence Platform (Decision Support for Human Adjudication)  
**Date:** September 2026  
**Status:** Complete & Validated (65/65 Pytest Passing, TypeScript Clean, Frontend Build Green)  

---

## 1. Executive Summary

Phase 06 establishes the project's first unified **Multi-Modal Incident Evidence Dossier** (`IncidentEvidenceDossier`). 

In Phase 05, the deterministic reconstruction engine extracted empirical interaction episodes with 100% recall across official FIA reference incidents. Phase 06 synthesizes those raw candidate telemetry segments with all surrounding investigation modalities:
1. **Compact Telemetry Evidence:** Sensor convergence, minimum proximity, closing rates, longitudinal deceleration differentials, and data fidelity metrics (interpolation vs. raw coverage).
2. **Chronological Milestone Timeline:** A sequence of key tactical events ($T-2.0\text{s}$ approach, $T-0.8\text{s}$ braking onset, $T+0.0\text{s}$ minimum proximity apex, $T+2.0\text{s}$ exit/stabilization).
3. **Race Control Notices:** Chronological correlation with official FIA race control messages and flag conditions, indexed with relative $\Delta t$ to event peak.
4. **Video Evidence & Synchronization:** Source-agnostic mathematical translation between session UTC wall-clock time and video playback timestamps, with clip boundaries and honest handling of unavailable broadcast feeds.
5. **Statutory Regulation Linkages:** Deterministic mapping of empirical interaction characteristics to relevant articles of the FIA Formula One Sporting Regulations (e.g. Article 33.4) and International Sporting Code Appendix L (Chapter IV, Articles 2(b) & 2(d)).
6. **Audit Provenance:** An immutable provenance record for every evidentiary claim.
7. **Decoupled Evidence Dimensions:** Separate reporting of telemetry strength, race control correlation, video synchronization status, and regulatory applicability—strictly avoiding misleading composite scores.

---

## 2. Core Jurisprudential Doctrine

> [!IMPORTANT]
> **AI Assists. Evidence Supports. Humans Decide.**
> Under no circumstances does the MII platform determine sporting guilt, driver fault, liability, or penalties. The dossier provides structured empirical intelligence designed exclusively to accelerate deliberation by appointed **Human FIA Race Stewards**. All narrative outputs, regulation links, and timeline milestones use neutral observational terminology.

---

## 3. Architecture of Multi-Modal Dossier Fusion

```
Raw Multi-Rate Sensor Streams (FastF1 / OpenF1)
                     ↓
        25 Hz Uniform SI Grid
                     ↓
   Deterministic Multi-Signal Candidate
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              IncidentEvidenceDossier                        │
│                                                             │
│  ├─ TelemetryEvidenceSummary    (25Hz SI Convergence)      │
│  ├─ TimelineMilestones          (Chronological Sequence)    │
│  ├─ RaceControlEvidenceSummary  (FIA Notice & Flag Alignment)│
│  ├─ VideoEvidenceSummary        (UTC ↔ Playback Math Sync)  │
│  ├─ RegulationEvidenceSummary   (Statutory Reference Links) │
│  ├─ EvidenceProvenanceRecord    (Auditability per Channel)  │
│  └─ Decoupled EvidenceDimensions (Independent Metrics)      │
└─────────────────────────────────────────────────────────────┘
                     ↓
   convert_dossier_to_frontend_incident()
                     ↓
   Frontend IncidentDetailResponse Contract
```

---

## 4. Evidentiary Sub-Layers

### 4.1 Telemetry Evidence Summary (`TelemetryEvidenceSummary`)
- **Location:** `backend/app/evidence/telemetry_evidence.py`
- **Purpose:** Extracts empirical metrics without burdening downstream consumers with thousands of raw coordinates.
- **Key Parameters Extracted:**
  - `minimum_gap_meters`: Closest Euclidean 3D proximity during the interaction window.
  - `peak_closing_speed_ms`: Maximum rate of approach $-d(\text{gap})/dt$.
  - `speed_a_kmh`, `speed_b_kmh`, `speed_delta_kmh`: Speeds at apex moment.
  - `throttle_a_pct`, `throttle_b_pct`, `brake_a_pct`, `brake_b_pct`: Pedal application percentages.
  - `brake_delta_pct`: Disparity in braking effort.
  - `total_frames`, `data_coverage_pct`, `interpolation_pct`, `missing_data_pct`: Full transparency on FastF1 ~3.5 Hz upsampling onto 25 Hz lattice.
  - `raw_stream_ref`: URL linking directly to the full 25Hz timeseries pair stream.

### 4.2 Chronological Event Timeline (`TimelineMilestone`)
- **Location:** `backend/app/evidence/timeline.py`
- **Purpose:** Organizes the interaction into a clear temporal sequence relative to the peak moment ($T+0.0\text{s}$):
  - **$T-2.0\text{s}$ (Approach Phase):** Initial high-speed positioning before deceleration.
  - **$T-2.0\text{s}$ to $T-1.0\text{s}$ (Peak Closing Velocity):** Maximum relative approach velocity between vehicles.
  - **$T-0.8\text{s}$ (Braking Onset):** Initiation of threshold braking by either competitor.
  - **$T+0.0\text{s}$ (Minimum Proximity Apex):** Closest spatial convergence.
  - **$T+2.0\text{s}$ (Separation & Corner Exit):** Trajectory divergence and post-apex recovery.

### 4.3 Race Control Context (`RaceControlEvidenceSummary`)
- **Location:** `backend/app/evidence/race_control_evidence.py`
- **Purpose:** Correlates official FIA race control messages with relative timing $\Delta t$ from candidate peak:
  - Tracks sector flags (`YELLOW`, `GREEN`, `CHEQUERED`) and track statuses (`VSC`, `SAFETY CAR`).
  - Correlates steward notifications (`"INCIDENT INVOLVING CARS 3 (RIC) AND 27 (HUL) NOTED"`).
  - Explicitly states: *"Race control messages reflect official steward room activity and flag status. They provide supporting contextual evidence and do not constitute automated guilt determination."*

### 4.4 Video Synchronization Architecture (`VideoEvidenceSummary`)
- **Location:** `backend/app/evidence/video_evidence.py`
- **Status Enum:**
  - `VIDEO_SYNCHRONIZED`: Calibrated sub-second alignment between video and session time.
  - `VIDEO_AVAILABLE`: Footage exists but has not been time-locked.
  - `VIDEO_UNSYNCHRONIZED`: Clock drift or unknown epoch offset.
  - `VIDEO_UNAVAILABLE`: No verified broadcast stream available.
- **Copyright Compliance & Video Reality:**
  - The repository contains only a promotional hero background video (`This is Formula One...mp4`); no commercial FOM broadcast race footage for Monza Turn 4 is stored.
  - Per strict user instructions, missing video is reported **honestly** as `VIDEO_UNAVAILABLE`.
  - When verified footage is provided, the mathematical sync model computes:
    $$\text{video\_time} = (\text{session\_utc} - \text{session\_to\_video\_offset\_sec}) \times \text{time\_scale}$$
    with pre-roll and post-roll buffers to generate exact clip recommendations (`clip_start_video_time`, `clip_peak_video_time`, `clip_end_video_time`).

### 4.5 Statutory Regulation Evidence & Linkages (`RegulationEvidenceSummary`)
- **Location:** `backend/app/evidence/regulation_evidence.py`
- **Matched Provisions:**
  - **FIA ISC Appendix L, Chapter IV, Article 2(d) (Causing a Collision):** Triggered when minimum gap $\le 3.5\text{m}$ (potential wheel overlap).
  - **FIA ISC Appendix L, Chapter IV, Article 2(b) (Crowding off Track):** Triggered for corner-entry proximity, directing stewards to evaluate racing room.
  - **FIA Sporting Regulations Article 33.4 (Erratic / Dangerous Driving):** Triggered when differential deceleration $\ge 2.0\text{G}$.
  - **FIA Sporting Regulations Article 33.3 (Track Limits & Leaving Track):** Triggered on trajectory deviation.
- **Bidirectional Links (`EvidenceRegulationLink`):** Connects observed physical telemetry data to specific steward review actions (e.g. *"Examine camera footage to determine whether contact occurred and assess apex ownership under Driving Standards Guidelines"*).

### 4.6 Audit Provenance (`EvidenceProvenanceRecord`)
- **Location:** `backend/app/evidence/provenance.py`
- **Purpose:** Records metadata for each evidence source:
  - Source identifier and dataset version.
  - Processing methodology (e.g., *"25 Hz uniform grid resampling with monotonic deduplication"*).
  - Ingestion timestamp and verification checksums.

---

## 5. Decoupled Evidence Dimensions

Rather than collapsing disparate evidence modalities into an arbitrary composite percentage, the system exposes four orthogonal dimensions:

```python
class EvidenceDimensions(BaseModel):
    telemetry_evidence_strength: int      # 0-100 (Physical sensor convergence)
    race_control_context_strength: int    # 0-100 (FIA steward notification alignment)
    video_evidence_status: VideoSyncStatus # VIDEO_UNAVAILABLE / VIDEO_SYNCHRONIZED
    regulation_reference_status: str      # APPLICABLE_STATUTORY_PROVISIONS_IDENTIFIED
```

This prevents situations where missing video artificially lowers telemetry confidence, or where a yellow flag notice inflates physical proximity certainty.

---

## 6. Official Ground-Truth Reference Case Evaluations

The multi-modal dossier was evaluated against the 2024 Italian Grand Prix ground truth cases:

| Case ID | Drivers | Lap | Turn | Official FIA Document | Telemetry Convergence | Race Control Correlation | Video Status | Matched Regulations |
|:---|:---|:---:|:---:|:---|:---:|:---:|:---:|:---|
| **REF-MONZA-01** | RIC vs HUL | 1 | 4 | Document 54 (10s Penalty) | **90%** (Min Gap: 0.04m, $8.8\text{ m/s}$) | Correlated (Incident Noted) | `VIDEO_UNAVAILABLE` | ISC App L 2(d), 2(b) |
| **REF-MONZA-02** | HUL vs TSU | 4 | 1 | Document 55 (10s Penalty) | **90%** (Min Gap: 0.03m, $10.1\text{ m/s}$) | Correlated (Incident Noted) | `VIDEO_UNAVAILABLE` | ISC App L 2(d), 2(b) |
| **REF-MONZA-03** | MAG vs GAS | 19 | 4 | Document 57 (10s Penalty) | **70%** (Min Gap: 13.55m, $2.4\text{ m/s}$) | Correlated (Yellow Flag) | `VIDEO_UNAVAILABLE` | ISC App L 2(d), 2(b) |

---

## 7. API Endpoints Implemented

1. **`GET /api/v1/analysis/candidates/{candidate_id}/dossier`**
   - Returns the complete `IncidentEvidenceDossier`.
   - Supports active session candidate IDs (e.g., `CAND-2024-MON-RIC_HUL-L1-01`) as well as ground-truth reference aliases (`REF-MONZA-01`, `REF-MONZA-02`, `REF-MONZA-03`).
2. **`GET /api/v1/analysis/candidates/{candidate_id}/frontend-incident`**
   - Transforms the candidate dossier directly into the frontend `IncidentDetailResponse` contract.
3. **`GET /api/v1/incidents/{incident_id}`**
   - Augmented with transparent fallback: if an incident is not found in the SQL database, it automatically attempts resolution against the reconstruction engine.
   - For database incidents, enriches the response with real regulatory links and evidence-regulation connections.

---

## 8. Frontend Integration & Compatibility

- **Zero Frontend Visual Regressions:** No layout, CSS, animation, color, or component styling was modified.
- **Contract Fidelity:** `convert_dossier_to_frontend_incident` maps all dossier components into the existing TypeScript interfaces:
  - `evidenceAssessment`: Minimum proximity, closing speed, braking differential.
  - `relevantRegulations`: Mapped from FIA statutory database with `whyRelevant` and source links.
  - `evidenceConnections`: 3-step evidence $\rightarrow$ rule $\rightarrow$ steward action.
  - `timeline`: Visual milestones with icons and timestamps.
  - `uncertainties`: Explicit warnings regarding lack of onboard camera sync, GPS sampling limits, and human steward supremacy.

---

## 9. Verification & Quality Gates

1. **Backend Test Suite (Pytest):**
   - **65/65 tests passing** in 21.16s:
     - 10 new comprehensive dossier tests in `backend/app/tests/test_dossier.py`.
     - 8 candidate reconstruction tests in `test_evidence_reconstruction.py`.
     - 10 telemetry synchronization tests in `test_telemetry_service.py`.
     - 11 API route and contract tests in `test_routes.py`.
     - Plus all data ingestion, database, and schema validation tests.
2. **OpenAPI Schema Check:**
   - All 23 routes confirmed registered, including new dossier endpoints.
3. **Frontend Build & Typecheck:**
   - `npm run build`: Built in 10.95s with **0 errors**.
   - `npx tsc --noEmit`: Exited with code 0 and **0 errors**.

---

## 10. Conclusion & Recommended Next Step

With Prompt 06 complete, Motorsport Incident Intelligence now features a complete, validated, multi-modal evidence intelligence layer.

### RECOMMENDED PROMPT 07: CANDIDATE-TO-INCIDENT DATABASE PIPELINE & HUMAN STEWARD WORKFLOW
1. Implement automated ingestion from the reconstruction engine directly into the PostgreSQL/SQLite `incidents` table, enabling candidate dossiers to populate the Incident Explorer.
2. Connect the steward review workflow (`REQUIRES_REVIEW` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `REVIEWED`) with user-facing notes and rationale capture.
3. Wire the frontend toggle to allow live API consumption directly from FastAPI.
