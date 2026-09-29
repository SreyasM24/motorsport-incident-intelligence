# PROMPT 16 — MULTI-MODAL EVIDENCE SYNTHESIS, DISCREPANCY ANALYSIS & STEWARD DOSSIER REPORT

**Date:** 2026-09-28  
**Status:** PASS (COMPLETE & VERIFIED)  
**Backend Suite:** 205 passed, 0 failed (100% passing across Prompts 01–16)  
**Prompt 16 Dossier Suite:** 13 passed, 0 failed (`test_steward_dossier.py`)  
**Frontend TypeScript:** 0 errors (`tsc --noEmit` clean)  
**Frontend Production Build:** Built cleanly in 13.81s (`npm run build` clean)  

---

## 1. Executive Summary & System Purpose

Prompt 16 establishes the **Multi-Modal Evidence Synthesis, Discrepancy Analysis & Steward Evidence Dossier** layer for Motorsport Incident Intelligence. 

The primary mission of this system is to serve as an **evidence-intelligence and decision-support platform for human motorsport stewards**. It unifies eight independent and derived evidence streams collected across Prompts 01–15 into a single, structured, discrepancy-aware, machine-readable **Steward Evidence Dossier**.

### Strict Non-Adjudicative Mandate
In strict compliance with the core philosophy of Motorsport Incident Intelligence:
- The system **OBSERVES**, **RECONSTRUCTS**, **QUANTIFIES**, and **PRESENTS EVIDENCE**.
- The system **DOES NOT**:
  - Assign fault or guilt.
  - Determine driver intent or culpability.
  - Predict or recommend steward verdicts.
  - Issue automatic penalties or regulatory violation flags.
  - Generate composite "guilt scores", "incident scores", "violation probability", or "fault percentages".
- **Human Stewards** remain the sole adjudicators and decision-makers.

---

## 2. Evidence Architecture & 8-Stream Synthesis

The synthesizer collates evidence across eight distinct streams, preserving clear epistemic status for every piece of information:

| # | Stream Name | Originating Subsystem | Epistemic Type | Description |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Telemetry Dynamics** | Ingestion & Preprocessing (Prompts 03–04.1) | `OBSERVED` | Canonical speeds, throttle, braking pressure, RPM, gear, steering angle |
| 2 | **Spatial & Trajectory** | Incident Reconstruction (Prompt 05) | `DERIVED` | World $(X,Y)$ positions, Euclidean gap distance, lateral closing rate |
| 3 | **Reference Lap Baseline** | Reference Baseline Service (Prompt 08) | `DERIVED` | Delta speed, braking onset distance offset from clean personal/session laps |
| 4 | **Cornering Overtake Geometry** | Geometry & Apex Service (Prompt 09) | `DERIVED` | Corner phase, lateral track width share, longitudinal overlap ratio |
| 5 | **ML Interaction Resemblance**| Trained Resemblance Model (Prompts 10–11) | `MODEL_DERIVED` | Feature distance to known interaction topologies (no guilt inference) |
| 6 | **Video Provenance & Clocks** | Video Synchronization Engine (Prompt 12) | `OBSERVED` | Timecode mapping, camera calibration, sync uncertainty bounds |
| 7 | **Visual Features & Tracks** | Visual & CV Tracking Engines (Prompts 13–15)| `MODEL_DERIVED` | Bounding box trajectories, visual closing rates, bounding box IoU |
| 8 | **FIA Statutory Regulations** | Statutory Knowledge Graph (Prompt 06) | `DOCUMENTARY` | Non-binding references to FIA ISC App L and F1 Sporting Regulations |

---

## 3. Epistemic Classification & Lineage Tracking

To prevent cognitive bias and artificial amplification of confidence, the framework explicitly enforces:

### 3.1 Epistemic Status Types
- `OBSERVED`: Direct empirical measurements from physical sensors or calibrated camera clocks (e.g. wheel speeds, GPS coordinates, video timecodes).
- `DERIVED`: Mathematically computed kinematic or geometric metrics derived deterministically from sensor streams (e.g. Euclidean distance, apex overlap ratio).
- `MODEL_DERIVED`: Inferences or predictions produced by statistical or neural models (e.g. ML interaction feature resemblance, CV object detector bounding boxes).
- `DOCUMENTARY`: Regulatory articles, session metadata, or official timing notices.
- `UNAVAILABLE`: Honestly reported unobserved or missing streams (e.g. copyrighted video feeds, uncalibrated footage).

### 3.2 Recursive Lineage & Non-Double-Counting (`LineageTracker`)
Derived features that originate from the same root sensor stream must **never** be counted as independent corroborating evidence.
- For example, min telemetry separation, relative speed delta, and apex overlap ratio all trace their root to the raw CAN-bus telemetry stream (`STREAM:TELEMETRY`).
- The `LineageTracker.compute_independent_observation_count` algorithm traces each item's `source_stream_ids` back to its root physical origins.
- If an incident dossier includes telemetry separation, reference baseline delta, and geometry overlap, the independent observation count is **1 root**, not 3. An independent video or timing loop stream is required to increment the root count to 2.

---

## 4. Cross-Modal Discrepancy & Consistency Analysis

The `ConsistencyEngine` deterministically cross-checks physical and visual streams against empirical thresholds.

### 4.1 Cross-Modal Checks
1. **Telemetry vs. Visual Alignment:** Evaluates temporal offset between telemetry peak proximity and visual minimum bounding box distance. If offset exceeds $150\,\text{ms}$, a discrepancy is flagged.
2. **Geometry Apex Overlap vs. Telemetry Spatial Gap:** Checks whether an apex overlap classification (e.g. overlap $>0.50$) physically coincides with lateral proximity ($<2.5\,\text{m}$).
3. **Braking Onset vs. Clean Baseline:** Flags when car braking onset deviates by $>15.0\,\text{m}$ earlier or later than clean session baseline laps.
4. **Visual Stream Availability:** Identifies missing video streams (e.g. `REF-MONZA-01`) as honest gaps without penalizing telemetry confidence.

### 4.2 Discrepancy Severity Classifications
Discrepancy severities are strictly **empirical and technical alignment metrics**, NOT indicators of driver fault or guilt:
- `LOW`: Minor temporal phase difference ($\le 50\,\text{ms}$) or marginal geometry variation within expected sensor noise.
- `MEDIUM`: Noticeable divergence ($50\,\text{ms} - 150\,\text{ms}$) between telemetry peak deceleration and visual tracking or baseline variance.
- `HIGH`: Major physical contradiction ($> 150\,\text{ms}$ or telemetry indicates clear contact while visual track indicates $> 5\,\text{m}$ separation).
- `UNRESOLVED`: Incomplete or uncalibrated data preventing verifiable cross-modal reconciliation.

---

## 5. Dossier Structure & Deterministic Export

The `StewardEvidenceDossier` contract conforms to a standardized 14-section schema:
1. `dossier_id`: Unique canonical identifier (`DOSSIER-<candidate_id>`).
2. `candidate_id`: Canonical incident candidate ID.
3. `session_context`: Season, round, circuit, session type, session time.
4. `involved_drivers`: Primary and comparison driver codes and car numbers.
5. `human_review_status`: `REQUIRES_REVIEW`, `UNDER_REVIEW`, `REVIEWED`, or `DISMISSED` (strictly steward-controlled).
6. `consensus`: Summary consensus statement and overall consistency status (`HIGH_CONSISTENCY`, `MEDIUM_CONSISTENCY`, `DISCREPANCIES_DETECTED`, `INSUFFICIENT_DATA`).
7. `independent_observation_roots`: Exact count and list of physical sensor roots.
8. `quality_by_stream`: Array of 8 `EvidenceQualityRecord` objects detailing completeness, sample rate, calibration status, and latency.
9. `discrepancies`: List of `CrossModalDiscrepancy` objects with empirical descriptions and severity tags.
10. `timeline`: Chronological `NormalizedTimelineEvent` milestones (onset, braking delta, apex overlap, peak proximity, exit resolution).
11. `telemetry_evidence`: Raw and normalized kinematics summary.
12. `baseline_evidence`: Reference lap delta and braking onset offset.
13. `geometry_evidence`: Corner phase, overlap ratio, inside/outside lane allocation.
14. `regulations`: Descriptive links to relevant FIA statutory articles (ISC Appendix L Ch IV Art 2, Sporting Regulations Art 33.3).

### 5.1 Deterministic JSON Export
Accessible via:
- `GET /api/v1/analysis/candidates/{candidate_id}/steward-dossier/export/json`
- `GET /api/v1/incidents/{incident_id}/dossier/export/json`

The JSON payload includes formatted export timestamps, schema versions, complete evidence items, quality records, discrepancies, and statutory notices for human panel presentation.

---

## 6. Monza 2024 Reference Cases Validation

The three Monza 2024 reference incidents (`REF-MONZA-01`, `REF-MONZA-02`, `REF-MONZA-03`) were validated through the synthesis pipeline:

| Reference Case | Cars Involved | Circuit / Lap | Consistency Status | Independent Roots | Video Status | Human Review Status |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **REF-MONZA-01** | RIC (3) vs HUL (27) | Monza Turn 8 (Ascari) / L1 | `HIGH_CONSISTENCY` | 1 (`STREAM:TELEMETRY`) | `VIDEO_UNAVAILABLE` | `REQUIRES_REVIEW` |
| **REF-MONZA-02** | RUS (63) vs PER (11) | Monza Turn 1 (Prima Variante) / L34 | `HIGH_CONSISTENCY` | 1 (`STREAM:TELEMETRY`) | `VIDEO_UNAVAILABLE` | `REQUIRES_REVIEW` |
| **REF-MONZA-03** | MAG (20) vs GAS (10) | Monza Turn 4 (Variante della Roggia) / L52 | `HIGH_CONSISTENCY` | 1 (`STREAM:TELEMETRY`) | `VIDEO_UNAVAILABLE` | `REQUIRES_REVIEW` |

**Key Findings:**
- All reference cases properly synthesize with `candidate_id` overrides preserved.
- Missing video streams are honestly reported as `status: UNAVAILABLE` with FOM copyright notices; no fabricated visual tracks exist.
- Independent observation roots correctly register 1 root (`STREAM:TELEMETRY`), preventing derived spatial, baseline, and geometry features from artificially inflating consensus root counts.
- Initial review status defaults to `REQUIRES_REVIEW`, ensuring zero autonomous adjudication.

---

## 7. Frontend Integration (`StewardDossierPanel.tsx`)

The frontend was extended to provide an interactive, dark-mode, high-density dashboard for human stewards:
- **Header & Doctrine Alert:** Prominently displays non-adjudicative disclaimer stating that the system provides evidence only and that final decisions reside exclusively with the steward panel.
- **Consensus & Independent Roots Metric:** Badges showing overall consistency and independent observation count with root tags.
- **8-Stream Quality Grid:** Real-time cards displaying completeness %, sample rate, calibration status, and epistemic badge (`OBSERVED`, `DERIVED`, `MODEL-DERIVED`, `DOCUMENTARY`, `UNAVAILABLE`).
- **Discrepancy Inspector:** Color-coded severity table (`HIGH`, `MEDIUM`, `LOW`, `UNRESOLVED`) outlining cross-modal variances.
- **Normalized Timeline:** Step-by-step milestone list from incident onset to track exit resolution.
- **Granular Evidence Accordion:** Collapsible multi-modal inspector with value formatters, confidence ratings, and data lineage paths.
- **Deterministic JSON Export:** Dedicated button invoking `exportStewardDossierJson` and downloading formatted JSON dossiers.

---

## 8. Verification & Test Suite Summary

### 8.1 Prompt 16 Backend Tests (`app/tests/test_steward_dossier.py`)
- `test_lineage_tracker_root_deduplication`: Verified derived features sharing telemetry root count as 1 independent root.
- `test_consistency_engine_telemetry_vs_visual_aligned`: Verified alignment $<150\,\text{ms}$ produces no discrepancies.
- `test_consistency_engine_telemetry_vs_visual_discrepancy`: Verified divergence $>150\,\text{ms}$ flags `HIGH` severity discrepancy.
- `test_consistency_engine_geometry_telemetry_discrepancy`: Verified apex overlap without spatial proximity flags discrepancy.
- `test_synthesizer_monza_reference_cases`: Verified 14 sections across `REF-MONZA-01`, `02`, `03`.
- `test_synthesizer_honest_missing_video`: Verified missing video creates `UNAVAILABLE` record without crashing synthesizer.
- `test_synthesizer_descriptive_regulations`: Verified descriptive links to FIA ISC App L Ch IV Art 2.
- `test_dossier_export_payload_structure`: Verified deterministic JSON export serialization.
- `test_guardrail_no_fault_or_guilt_scores`: Verified zero occurrence of guilt scores, fault percentages, or autonomous verdicts.
- `test_api_candidate_steward_dossier_endpoint`: Verified `GET /candidates/{candidate_id}/steward-dossier`.
- `test_api_candidate_steward_dossier_export_json`: Verified `GET /candidates/{candidate_id}/steward-dossier/export/json`.
- `test_api_incident_dossier_endpoints`: Verified `GET /incidents/{incident_id}/dossier` and export endpoints.
- `test_backward_compatibility_prompt06_dossier`: Verified original Prompt 06 endpoint remains intact.

**Result: 13 / 13 PASSED** (0.42s)

### 8.2 Full Backend Regression Suite
- Ran `python -m pytest app/tests -v` across all 16 prompts.
- **Result: 205 PASSED, 0 FAILED** (667.71s)

### 8.3 Frontend Build & Lint Verification
- `npm run lint` (`tsc --noEmit`): **0 errors**.
- `npm run build` (`vite build`): **Built cleanly in 13.81s**.

---

## 9. Environmental Notes

- **PostgreSQL Database:** As in previous prompts, PostgreSQL was not locally available during test execution; SQLite was utilized via the existing test fixture architecture in `conftest.py`.
- **FastF1 Telemetry Cache:** Pre-cached session files under `data/fastf1_cache/` were used for telemetry reconstruction.
- **Video Copyright Compliance:** Certified synthetic test fixtures and simulated timelines were used for cross-modal validation; no commercial video files are distributed or hosted.

---

## 10. Conclusion & Prompt 16 Signoff

Prompt 16 is **COMPLETE, REGRESSION-FREE, AND VERIFIED**.
The system now provides motorsport stewards with a transparent, lineage-tracked, discrepancy-aware evidence dossier that unifies all physical, spatial, baseline, ML, video, visual, CV, and regulatory evidence streams while strictly preserving the non-adjudicative role of the human panel.
