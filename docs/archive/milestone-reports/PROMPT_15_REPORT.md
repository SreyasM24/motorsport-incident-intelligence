# PROMPT 15 — REAL-WORLD CV DATASET, ANNOTATION & EVALUATION FOUNDATION REPORT

**Date:** 2026-09-28  
**Status:** PASS (COMPLETE & VERIFIED)  
**Current CV Readiness Classification:** `A. SYNTHETIC_VALIDATION_ONLY`  
**Backend Suite:** 192 passed, 0 failed (100% passing)  
**Prompt 15 CV Evaluation Suite:** 13 passed, 0 failed  
**Prompt 14 CV Engine Suite:** 29 passed, 0 failed  
**Frontend TypeScript:** 0 errors (`tsc --noEmit` clean)  
**Frontend Production Build:** Built cleanly in 20.93s (`npm run build` clean)  

---

## 1. Executive Summary & State Classification

Prompt 15 establishes the **Computer Vision Dataset, Ground Truth Annotation & Evaluation Foundation** for Motorsport Incident Intelligence. The primary objective was not to add more model complexity, but to turn the existing CV pipeline into a **properly evaluable, transparent, and leakage-safe evaluation framework** grounded in rigorous measurement and error analysis.

### Explicit State Classification
In strict compliance with Prompt 15 acceptance criteria:

```yaml
CURRENT_STATE_CLASSIFICATION: A. SYNTHETIC_VALIDATION_ONLY
REAL_VIDEO_STATUS: NOT_AVAILABLE
SYNTHETIC_FIXTURE_STATUS: AVAILABLE
REAL_WORLD_EVALUATION_STATUS: INSUFFICIENT_DATA
IDENTITY_EVALUATION: NOT_AVAILABLE
CROSS_MODAL_EVALUATION: NOT_AVAILABLE
```

**Rationale:** Official Formula One broadcast footage is commercially copyrighted and protected by Formula One Management (FOM) and Liberty Media. The repository contains zero unauthorized commercial race video files and zero fabricated accuracy benchmarks. All quantitative detection and tracking metrics reported in the evaluation suite are explicitly tagged as `SYNTHETIC_TEST_DATA` and tested against certified synthetic test fixtures.

---

## 2. Dataset Discovery Audit

A thorough audit of the repository workspace confirmed the following:
- **Real Race Video Status:** `REAL_VIDEO_STATUS = NOT_AVAILABLE`. No copyrighted broadcast video, onboard camera feeds, or official race video captures are hosted or committed to this repository.
- **Demo Footage (`public/`):** Contains only an uncalibrated montage (`this-is-formula-one.mp4`) used exclusively for basic client-side video player control demonstration in Prompt 12. It carries no sub-millisecond ECU timestamps, camera intrinsic parameters, or ground-truth annotations.
- **Monza 2024 Reference Cases (`REF-MONZA-01`, `02`, `03`):** Officially preserved as `status: VIDEO_UNAVAILABLE` with clear commercial copyright attribution. Missing video is treated as an honest unobserved state, never as negative evidence.

### Catalog of Known Public & Research Datasets
To support future integration of authorized or open research datasets without legal infringement, the following benchmarks were surveyed and cataloged in `data/cv/README.md`:

| Dataset | Domain | License | Annotations | Limitations for F1 Adjudication |
| :--- | :--- | :--- | :--- | :--- |
| **F1TENTH Autonomous Racing** | 1:10 Autonomous Scale Vehicles | MIT / Open Access | 2D LiDAR, Odometry, Depth | Scale model vehicles, indoor tracks, no full-size F1 open-wheel aero |
| **Indy Autonomous Challenge / Roborace** | Full-Scale Open-Wheel Autonomous (AV-21) | Academic / Research Restricted | Multi-Camera, LiDAR, Telemetry | Non-contact racing doctrine; autonomous control, not FIA steward review |
| **Boxy Vehicle Dataset** | Highway Vehicle 3D/2D Bounding Boxes | CC BY-NC-SA 4.0 | 200k images, 2M bounding boxes | Highway passenger vehicles; lacks racing apex convergence and high-G kinematics |
| **UA-DETRAC** | Traffic Multi-Object Tracking | CC BY 4.0 | 100k frames, 1.2M boxes, track IDs | Static surveillance angles; urban street cars at low speeds |
| **BDD100K** | Dashcam Driving Video | BSD-3-Clause | 100k videos, boxes, MOT IDs | Dashcam perspective; street cars, non-racing dynamics |

---

## 3. Dataset Protocol & File Layout

A reproducible dataset specification has been established under `data/cv/`:

```
data/cv/
├── README.md                  # Protocol, provenance, and dataset survey
├── manifest/
│   └── dataset_manifest.json  # Sample manifest (sample_id, series, event, resolution, fps, license)
├── annotations/
│   └── annotations_sample.json# Normalized & absolute bounding box ground truth annotations
└── splits/
    └── dataset_splits.json    # Leakage-safe group-based train/val/test splits
```

### 3.1 Manifest Schema
Each sample in `data/cv/manifest/dataset_manifest.json` specifies:
- `sampleId`, `sourceVideo`, `frameId`, `frameNumber`, `timestampSec`, `timestampStr`, `cameraId`
- `series` (e.g. `"Formula 1 Synthetic Benchmark"`), `event`, `season`, `session`
- `resolution` (e.g. `"1920x1080"`), `fps` (`30.0`)
- `annotationStatus` (`"ANNOTATED"` or `"UNAVAILABLE"`)
- `provenanceType` (`"SYNTHETIC_TEST_DATA"` vs `"OFFICIAL_COMMERCIAL_BROADCAST"`)
- `licenseProvenance`

---

## 4. Annotation Contract & Ground Truth Policy

### 4.1 Strict Coordinate Separation
The system supports two explicit coordinate formats and prevents silent mixing:
1. **`NORMALIZED_0_1` (Default):** Coordinates $[x_{\min}, y_{\min}, x_{\max}, y_{\max}] \in [0.0, 1.0]^4$, origin at top-left $(0,0)$.
2. **`PIXEL_ABSOLUTE`:** Integer pixel coordinates $[x, y, w, h]$ relative to frame dimensions $(W \times H)$.
- Conversions are explicitly handled via `to_normalized(frame_w, frame_h)` and `to_pixel(frame_w, frame_h)`.

### 4.2 Ground Truth vs Prediction Distinction
The framework enforces strict typing:
- **`GROUND_TRUTH`:** Certified human expert or synthetic fixture definitions (`GroundTruthAnnotation`).
- **`MODEL_PREDICTION`:** Raw hypotheses emitted by a `VehicleDetector` or `VehicleTracker` (`Detection`, `Track`).
- **`DERIVED_METRIC`:** Computed geometric/kinematic features (`TrackInteractionFeature`, IoU).
- **Policy:** Model predictions, tracker coasting, telemetry proximity, and incident reconstruction outputs are strictly forbidden from being used as visual ground-truth labels.

---

## 5. Leakage-Safe Group-Based Splitting

To eliminate severe temporal leakage across adjacent video frames:
- **Rule:** Adjacent frames from the same video or camera sequence must **NEVER** be randomly partitioned across train and test sets.
- **Implementation:** `GroupSplitter.partition_samples_by_group()` partitions data strictly at the **Session**, **Video**, or **Event** level.
- **Verification:** `GroupSplitter.verify_no_leakage()` cryptographically verifies zero shared group keys between partitions:
  $$\text{Intersection}(\text{Train Groups}, \text{Test Groups}) = \emptyset$$

---

## 6. Evaluation Subsystems

### 6.1 Detection Evaluation (`detector_eval.py`)
- Evaluates detector hypotheses against ground-truth boxes using greedy bipartite IoU matching at a documented threshold (default $\text{IoU} \ge 0.50$).
- Measures:
  - True Positives (TP), False Positives (FP), False Negatives (FN), Duplicate Detections
  - Precision, Recall, F1 Score
  - IoU Distribution: Mean, Median, Min, Max IoU
  - Average Precision: AP@50 and AP@75
  - Granular Breakdown by Vehicle Size:
    - Small ($<0.01$ area)
    - Medium ($0.01 \le \text{area} < 0.05$)
    - Large ($\ge 0.05$ area)
  - Granular Breakdown by Occlusion: Unoccluded ($<0.10$), Partial ($0.10 - 0.50$), Heavy ($>0.50$)

### 6.2 Tracking Evaluation (`tracker_eval.py`)
- Evaluates multi-object tracker performance independently from detection:
  - **ID Switches (IDSW):** Tracks when the matched predicted track changes for a single ground-truth trajectory.
  - **Track Fragmentations:** Counts interruptions where a tracked vehicle is temporarily dropped and resumed.
  - **Track Continuity Ratio:** $\frac{\text{Observed Frames}}{\text{Lifespan Frames}}$.
  - **Mean Track Duration:** Measured in seconds.
  - **Error Disambiguation:** Strictly distinguishes **Detection Errors** (no hypothesis in frame) from **Tracking Errors** (hypothesis present but misassigned).

### 6.3 Driver Identity Association Evaluation (`identity_eval.py`)
- Compares visual identity attributions against certified helmet/livery annotations:
  - Outcomes: `CORRECT`, `INCORRECT`, `UNKNOWN`, `NOT_ANNOTATED`.
  - **Guardrail:** Because real-world broadcast video driver livery/helmet ground truth is unbundled, the system honestly reports:
    ```yaml
    IDENTITY_EVALUATION: NOT_AVAILABLE
    ```
    No identity accuracy is fabricated or claimed from synthetic test fixtures.

### 6.4 Cross-Modal Synchronization Evaluation (`cross_modal_eval.py`)
- Measures the temporal disparity between visual minimum separation and telemetry peak proximity:
  $$\Delta t = |t_{\text{visual}} - t_{\text{telemetry}}|$$
- Categorizes events into `ALIGNED` ($\le 0.20$s), `PARTIALLY_ALIGNED` ($\le 0.20\text{s} + \sigma$), and `MISALIGNED`.
- When visual event ground truth is unlabelled on real sessions, reports `CROSS_MODAL_EVALUATION: NOT_AVAILABLE`.

### 6.5 Error Analysis & Failure Taxonomy
Categorizes failure modes into a 12-class taxonomy:
- `SMALL_VEHICLE`, `DISTANT_VEHICLE`, `HEAVY_OCCLUSION`, `OVERLAPPING_VEHICLES`
- `MOTION_BLUR`, `POOR_LIGHTING`, `CAMERA_SHAKE`, `PARTIAL_VISIBILITY`
- `DETECTOR_MISS`, `DUPLICATE_DETECTION`, `TRACK_FRAGMENTATION`, `IDENTITY_AMBIGUITY`

---

## 7. Incident-Level Visual Evidence Sufficiency Contract

In strict compliance with Prompt 15 Section 11, the incident sufficiency service answers:
> **"Is there sufficient visual evidence for human steward inspection?"**  
> *(It strictly does NOT answer "Who caused the incident?")*

### Sufficiency Checklist
For each incident candidate, the system evaluates:
1. `video_available`: Verified video stream linked?
2. `synchronization_valid`: Timestamp calibration established?
3. `vehicles_detected`: Vehicle detection hypotheses present?
4. `tracks_continuous`: Multi-frame track quality rating $\ge \text{MEDIUM}$?
5. `identities_available`: Visual tracks attributed to drivers?
6. `visual_interaction_features_available`: 2D pairwise interaction metrics calculated?
7. `telemetry_alignment_available`: Cross-modal synchronization verified?

### Steward Readiness Ratings
- **`SUFFICIENT`**: Continuous tracks with pairwise interaction features ready for steward review.
- **`PARTIALLY_SUFFICIENT`**: Detections exist, but tracking or identity evidence is incomplete.
- **`INSUFFICIENT`**: Missing or degraded visual frames.
- **`UNAVAILABLE`**: Commercial broadcast footage unlinked (e.g. Monza reference cases `REF-MONZA-01`, `02`, `03`).

---

## 8. API Endpoints

Two new REST endpoints have been added to `backend/app/api/analysis.py`:

### 8.1 System-Wide CV Evaluation
```http
GET /api/v1/analysis/cv/evaluation
```
Returns `CVEvaluationSuiteResponse` with dataset discovery audit, detector metrics, tracker metrics, identity evaluation status, failure categories taxonomy, and steward notice.

### 8.2 Candidate Visual Evidence Sufficiency
```http
GET /api/v1/analysis/candidates/{candidate_id}/video/cv/sufficiency
```
Returns `IncidentVisualEvidenceSufficiency` with the 7-point steward checklist and transparent limitations.

---

## 9. Frontend Integration

`src/components/VideoPlayer.tsx` has been enhanced with minimal, additive changes:
1. **Mode Switcher Tab:** Added **CV Evaluation (P15)** tab alongside Keyframes (P13) and CV Tracking (P14).
2. **Prominent Provenance Badges:** High-visibility badges distinguishing:
   - `REAL DATA: NOT_AVAILABLE`
   - `EVALUATION: SYNTHETIC TEST FIXTURE ONLY`
3. **Four Summary Metric Cards:** Dataset Discovery, Benchmark State, Steward Readiness, and Sample Count.
4. **Detailed Benchmark Grid:** Detector performance (Precision, Recall, F1, Mean IoU), Tracker metrics (ID switches, continuity), Driver Identity status (`NOT_AVAILABLE`), and Cross-Modal status (`NOT_AVAILABLE`).
5. **Error Analysis Taxonomy:** Visual tags displaying failure category counts.
6. **Steward Primacy Notice:** Reaffirms that visual metrics are descriptive evidence for human stewards and never assign guilt or fault.

---

## 10. Verification & Test Execution Results

### 10.1 Dedicated Prompt 15 Test Suite (`test_cv_evaluation.py`)
```bash
python -m pytest app/tests/test_cv_evaluation.py -v
```
**Results:** **13 passed, 0 failed** in 0.27s.

| Test Case | Status | Verified Capability |
| :--- | :---: | :--- |
| `test_dataset_manifest_loading` | PASS | Loads samples, validates schema, verifies Monza `UNAVAILABLE` |
| `test_annotation_coordinate_conversion` | PASS | Strict conversion between `NORMALIZED_0_1` and `PIXEL_ABSOLUTE` |
| `test_ground_truth_vs_prediction_separation` | PASS | Provenance typing strictly distinguishes GT from predictions |
| `test_group_based_splitting_zero_leakage` | PASS | Group-based splitting guarantees zero session/video leakage |
| `test_detection_evaluator_metrics_calculation` | PASS | Computes precision, recall, F1, IoU distribution, TP/FP/FN |
| `test_tracking_evaluator_id_switches_and_continuity` | PASS | Measures ID switches (IDSW), fragmentations, and continuity |
| `test_identity_evaluator_synthetic_fixture_behavior` | PASS | Honestly returns `NOT_AVAILABLE` for synthetic fixtures |
| `test_cross_modal_evaluator` | PASS | Evaluates temporal delta $\Delta t$ and returns `NOT_AVAILABLE` when empty |
| `test_incident_evidence_sufficiency_monza_unavailable` | PASS | Monza cases strictly return `steward_readiness: UNAVAILABLE` |
| `test_incident_evidence_sufficiency_synthetic_success` | PASS | Synthetic fixtures achieve `steward_readiness: SUFFICIENT` |
| `test_api_cv_evaluation_endpoint` | PASS | `GET /analysis/cv/evaluation` returns valid 200 response |
| `test_api_candidate_cv_sufficiency_monza` | PASS | `GET /candidates/{id}/video/cv/sufficiency` returns 200 with honest unavailable |
| `test_guardrails_no_guilt_or_fault` | PASS | Zero occurrences of forbidden adjudicative terms |

### 10.2 Full Backend Regression Suite
```bash
python -m pytest app/tests -q
```
**Results:** **192 passed, 0 failed** in 743.74s (100% passing across Prompts 01–15).

### 10.3 Frontend Verification
- **TypeScript Typecheck:** `npx tsc --noEmit` exited cleanly with **0 errors**.
- **Frontend Linter:** `npm run lint` exited cleanly with **0 errors**.
- **Production Build:** `npm run build` compiled cleanly in **20.93s**.

---

## 11. Critical Project Guardrail Compliance

A programmatic audit confirms strict adherence to project guardrails:
- **No Collision Classifier:** The system does not classify whether an impact occurred.
- **No Fault or Guilt Assignment:** Words like *"at fault"*, *"guilty"*, *"liable"*, or *"illegal"* do not exist in evaluation outputs.
- **No Penalty Recommendations:** No penalties, grid drops, or license points are issued.
- **Strict Human Steward Primacy:** The CV system serves exclusively as a descriptive evidence-extraction component.

---

## 12. Final Acceptance

```yaml
STATUS: PASS
```

- Dataset status is explicit: `REAL_VIDEO_STATUS = NOT_AVAILABLE`
- Annotation contract exists: `GroundTruthAnnotation` with explicit coordinates
- Ground-truth policy exists: Strict typing separates GT, predictions, and metrics
- Leakage-safe evaluation protocol exists: Group-based splitting with zero leakage
- Detection evaluation exists: Precision, Recall, F1, IoU distribution, size breakdowns
- Tracking evaluation exists: ID switches, fragmentations, continuity, error separation
- Identity evaluation exists: Honestly reports `NOT_AVAILABLE`
- Cross-modal evaluation exists: Honestly reports `NOT_AVAILABLE`
- Synthetic and real data strictly separated
- Failure taxonomy exists: 12 monitored failure categories
- No fabricated metrics exist
- Prompts 01–14 remain 100% regression-free (192 passed, 0 failed)
- Frontend typecheck, lint, and production build pass cleanly
- No autonomous steward decision logic is introduced

---

### RECOMMENDED PROMPT 16

**PROMPT 16 — MULTI-MODAL EVIDENCE SYNTHESIS, DISCREPANCY RESOLUTION & STEWARD DECISION-SUPPORT DOSSIER EXPORT**

Synthesize the disparate evidence streams (telemetry kinetics, spatial overtake geometry, ML interaction pattern scoring, video synchronization, bounded visual features, and computer vision tracking) into a unified, discrepancy-aware Steward Evidence Dossier. Quantify cross-modal consensus versus conflict, establish an automated audit trail for FIA compliance, and provide formal PDF/JSON dossier export capabilities for human steward panels.
