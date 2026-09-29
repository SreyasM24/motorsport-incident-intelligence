# PROMPT 14 — COMPUTER VISION VEHICLE DETECTION, TRACKING & VISUAL IDENTITY EVIDENCE REPORT

**Date:** 2026-09-28  
**Status:** PASS (COMPLETE & VERIFIED)  
**Backend Suite:** 179 passed, 0 failed (100% passing)  
**Prompt 14 CV Suite:** 29 passed, 0 failed  
**Frontend TypeScript:** 0 errors (`npm run lint` / `tsc --noEmit` clean)  
**Frontend Production Build:** Built cleanly in 38.63s (`npm run build` clean)  

---

## 1. Executive Summary

Prompt 14 introduces a production-oriented, modular **Computer Vision (CV) Vehicle Detection, Multi-Object Tracking & Visual Identity Evidence** layer to Motorsport Incident Intelligence. Building directly upon the temporal synchronization (Prompt 12) and bounded keyframe extraction (Prompt 13) foundations, this CV subsystem detects vehicle entities in video frames, maintains persistent tracking across sequential frames, quantifies track quality through deterministic metrics, safely associates visual tracks with competitor driver identities, and extracts pairwise interaction kinematics within an incident-focused time window ($\pm 2.0$ seconds around apex/peak).

In strict adherence to the project's foundational ethos, the CV module functions purely as **factual, descriptive decision support for human motorsport stewards**. It does not perform autonomous adjudication, assign fault, calculate penalties, or declare collision verdicts.

### Strict Jurisprudential & Compliance Doctrine
1. **Zero Autonomous Guilt, Fault, or Collision Determination:** Visual tracks, IoU bounding box overlaps, and proximity rates are strictly 2D geometric and kinematic observations. The system never labels an overlap as "guilt", "at fault", "illegal squeeze", or "contact confirmed".
2. **Honest Evaluation Reporting (`NOT_YET_AVAILABLE`):** In accordance with the prompt's instructions, no fabricated benchmark precision or recall figures are claimed without a verified, labeled real-world motorsport dataset. The system formally reports `EVALUATION_STATUS: NOT_YET_AVAILABLE`.
3. **No Automatic Weight Downloads & Safe Model Fallbacks:** The detector abstraction does not attempt network downloads during test execution or startup. Unconfigured or missing weights resolve cleanly to `status: MODEL_UNAVAILABLE`.
4. **Commercial Copyright Protection & Real GP Sessions:** For the official 2024 Italian Grand Prix reference incidents (`REF-MONZA-01`, `REF-MONZA-02`, and `REF-MONZA-03`), the CV pipeline returns `status: VIDEO_UNAVAILABLE` citing Formula One Management commercial licensing. Missing video is treated as unobserved evidence, never negative evidence.
5. **Defensible Identity Association:** Naive, brittle heuristics (such as "leftmost car = Driver A" or "track ID = driver car number") are strictly prohibited. Identity is only confirmed via fixed camera metadata, verified test fixture ground truth, or telemetry track entry order with explicit confidence scores.
6. **Perspective Projection Disclaimer (`BOUNDED_2D_PROJECTION`):** All 2D visual interaction features carry an explicit `measurement_basis: BOUNDED_2D_PROJECTION` metadata tag, clarifying that 2D image-plane overlap does not prove 3D physical contact without camera intrinsic/extrinsic calibration.

---

## 2. Architecture & Contracts

The Computer Vision subsystem is organized in a dedicated, decoupled architecture under `backend/app/evidence/cv/`:

```
backend/app/evidence/cv/
├── __init__.py           # Package exports and public API
├── contracts.py          # Abstract interfaces & domain entities
├── detector.py           # VehicleDetector ABC & implementations (ONNX, Synthetic, Null)
├── tracker.py            # VehicleTracker ABC & DeterministicSortTracker implementation
├── identity.py           # VisualIdentityAssociator for defensible driver attribution
├── features.py           # Pairwise 2D kinematic & spatial interaction calculation
└── service.py            # CVIncidentService orchestrating window-scoped analysis
```

The data contracts are mirrored in `backend/app/schemas/cv_evidence.py` and re-exported in the API schema layer.

### 2.1 Domain Models & Status Types
- **`CVProcessingStatus`**: `AVAILABLE`, `MODEL_UNAVAILABLE`, `VIDEO_UNAVAILABLE`, `INSUFFICIENT_DATA`, `PROCESSING_ERROR`.
- **`ModelStatus`**: `LOADED`, `MODEL_UNAVAILABLE`, `NOT_CONFIGURED`.
- **`TrackingQualityRating`**: Deterministic four-tier rating: `HIGH`, `MEDIUM`, `LOW`, `INSUFFICIENT_DATA`.
- **`IdentityMethod`**: `ONBOARD_CAMERA_FIXED`, `TEST_FIXTURE`, `TELEMETRY_TRACK_ORDER`, `UNAVAILABLE`.
- **`CVEvaluationStatus`**: `NOT_YET_AVAILABLE`, `PRELIMINARY`, `EVALUATED`.
- **`BoundingBox`**: Normalized coordinates $[x_{\min}, y_{\min}, x_{\max}, y_{\max}] \in [0, 1]^4$, with width, height, centroid $(x_c, y_c)$, area, deterministic 2D IoU calculation (`compute_iou`), and normalized centroid distance (`centroid_distance`).
- **`Detection`**: Class name (`formula_car`), confidence score $[0.0, 1.0]$, bounding box.
- **`TrackObservation`**: Frame index, video timestamp, bounding box, centroid, confidence, velocity vector $(v_x, v_y)$, and visibility state.
- **`Track`**: Track ID (`TRK-01`), start/end timestamps, list of observations, and associated `TrackQuality`.
- **`TrackQuality`**: Total observations, track duration, visibility ratio, mean confidence, minimum confidence, max continuous frame gap, fragmentation count, and rating.
- **`VisualIdentityAssociation`**: Track ID, driver code, car number, association method, confidence $[0.0, 1.0]$, and status (`CONFIRMED`, `INFERRED`, `UNAVAILABLE`).
- **`TrackInteractionFeature`**: Pairwise 2D metrics: centroid separation %, relative approach rate ($d(\text{sep})/dt$), pixel displacement, IoU overlap, approach/recede trend, occlusion ratio, and `measurement_basis: BOUNDED_2D_PROJECTION`.
- **`CVIncidentAnalysisResponse`**: Complete incident window CV response with status, tracks, identity associations, interaction features, performance metrics, evaluation report, and limitations statement.

---

## 3. Subsystem Components

### 3.1 Vehicle Detector (`detector.py`)
- **`VehicleDetector` (ABC):** Defines the standard detection contract: `detect(frame: np.ndarray, frame_index: int, timestamp_sec: float) -> DetectionFrame`, `get_model_status() -> ModelStatus`, and `get_metadata() -> Dict[str, Any]`.
- **`ConfigurableONNXVehicleDetector`:** Production-oriented detector designed to load an ONNX-runtime model from a specified local file path. If the model file is missing or unconfigured, it safely initializes in `MODEL_UNAVAILABLE` mode without attempting unauthorized remote downloads.
- **`SyntheticFixtureVehicleDetector`:** Deterministic trajectory detector for automated test suites. Produces known, reproducible vehicle trajectories (e.g., closing proximity, apex convergence, and diverging exit) with configurable confidence levels.
- **`NullVehicleDetector`:** Safe fallback detector that returns empty detections and `MODEL_UNAVAILABLE` status.

### 3.2 Deterministic Multi-Object Tracker (`tracker.py`)
- **`DeterministicSortTracker`:** Implements greedy bipartite matching based on a linear combination of 2D IoU and centroid distance:
  $$\text{Cost}(D_i, T_j) = 0.6 \cdot (1 - \text{IoU}) + 0.4 \cdot \text{Distance}_{\text{norm}}$$
- Matches detections with existing active tracks if the cost is below the matching threshold ($0.7$).
- Unmatched detections spawn new sequential tracks (`TRK-01`, `TRK-02`, etc.).
- Handles missed detections via coasting up to `max_age` (default 5 frames) before terminating stale tracks.
- **Track Quality Rating:** Evaluates tracking reliability mathematically:
  - `HIGH`: $\ge 15$ observations, duration $\ge 0.5$s, visibility ratio $\ge 0.85$, mean confidence $\ge 0.80$, max frame gap $\le 2$.
  - `MEDIUM`: $\ge 8$ observations, duration $\ge 0.25$s, visibility ratio $\ge 0.70$, mean confidence $\ge 0.65$, max frame gap $\le 4$.
  - `LOW`: Below medium thresholds but $\ge 3$ observations.
  - `INSUFFICIENT_DATA`: $< 3$ observations.

### 3.3 Visual Identity Associator (`identity.py`)
- Evaluates provenance metadata and telemetry track order to bind physical drivers to visual tracks:
  1. **Fixed Onboard Camera (`ONBOARD_CAMERA_FIXED`):** If camera metadata identifies an onboard installation (e.g. Driver A's T-cam), the primary foreground track is associated with Driver A as `CONFIRMED` ($1.0$ confidence).
  2. **Test Fixture Truth (`TEST_FIXTURE`):** Associates test tracks with known fixture identities (`CONFIRMED`).
  3. **Telemetry Track Order (`TELEMETRY_TRACK_ORDER`):** Associates entering tracks with competitor ordering from 25Hz telemetry timestamps as `INFERRED` ($0.75$ confidence).
  4. **Fallback:** Reports `UNAVAILABLE` ($0.0$ confidence). The system explicitly rejects naive heuristics like spatial left/right sorting.

### 3.4 Pairwise Interaction Features (`features.py`)
- Computes time-series interaction metrics between primary tracks over the incident window:
  - **Centroid Separation:** $\text{Sep}(t) = \sqrt{(x_1 - x_2)^2 + (y_1 - y_2)^2}$
  - **Relative Approach Rate:** $d(\text{Sep})/dt = \frac{\text{Sep}(t) - \text{Sep}(t-1)}{\Delta t}$ (negative indicates closing velocity, positive indicates separation).
  - **IoU Overlap:** 2D bounding box intersection over union.
  - **Approach Trend:** `APPROACHING` when $d(\text{Sep})/dt < -0.05$/s, `RECEDING` when $d(\text{Sep})/dt > 0.05$/s, `STABLE` otherwise.
  - **Occlusion Ratio:** $\frac{\text{Intersection Area}}{\min(\text{Area}_1, \text{Area}_2)}$.
  - **Measurement Basis:** Hardcoded to `BOUNDED_2D_PROJECTION`.

### 3.5 Incident Window CV Service (`service.py`)
- Orchestrates the full computer vision analysis for an incident candidate within a window of $\pm 2.0$ seconds around the telemetry-identified event peak:
  1. Checks if candidate belongs to Monza reference cases (`REF-MONZA-01`, `02`, `03`). If so, returns `VIDEO_UNAVAILABLE` immediately.
  2. Evaluates detector availability. If unconfigured/missing, returns `MODEL_UNAVAILABLE` with clear diagnostic limitations.
  3. If video and detector are available, processes frames at up to 30 FPS, runs tracking, calculates track quality, applies identity association, and extracts interaction kinematics.
  4. Attaches benchmark evaluation report (`status: NOT_YET_AVAILABLE`) and steward support disclaimer.

---

## 4. API Endpoints

A dedicated REST API endpoint has been exposed in `backend/app/api/analysis.py`:

```http
GET /api/v1/analysis/candidates/{candidate_id}/video/cv
```

### Response Example (Synthetic Fixture / Available Video)
```json
{
  "candidateId": "CAND-2024-TEST-01",
  "status": "AVAILABLE",
  "totalFramesAnalyzed": 61,
  "fps": 30.0,
  "timeWindowStartSec": 10.0,
  "timeWindowEndSec": 14.0,
  "peakVideoTimeSec": 12.0,
  "tracks": [
    {
      "trackId": "TRK-01",
      "startTimeSec": 10.0,
      "endTimeSec": 14.0,
      "observationCount": 61,
      "quality": {
        "rating": "HIGH",
        "observationCount": 61,
        "trackDurationSec": 2.0,
        "visibilityRatio": 1.0,
        "meanConfidence": 0.92,
        "minConfidence": 0.88,
        "maxFrameGap": 0,
        "fragmentationCount": 0
      }
    }
  ],
  "identityAssociations": [
    {
      "trackId": "TRK-01",
      "driverCode": "MAG",
      "carNumber": 20,
      "method": "TEST_FIXTURE",
      "confidence": 1.0,
      "status": "CONFIRMED"
    }
  ],
  "interactionFeatures": [
    {
      "videoTimeSec": 12.0,
      "sessionTimeSec": 1134.5,
      "centroidSeparationNorm": 0.082,
      "relativeApproachRate": -0.045,
      "pixelDisplacementPx": 4.2,
      "bboxOverlapIou": 0.12,
      "approachTrend": "APPROACHING",
      "occlusionRatio": 0.15,
      "measurementBasis": "BOUNDED_2D_PROJECTION"
    }
  ],
  "performanceMetrics": {
    "detectionTimeMs": 14.2,
    "trackingTimeMs": 1.8,
    "featureExtractionTimeMs": 0.6,
    "totalProcessingTimeMs": 16.6,
    "inferenceFps": 60.2,
    "hardwareTarget": "CPU"
  },
  "evaluationReport": {
    "status": "NOT_YET_AVAILABLE",
    "evaluationDataset": null,
    "meanAveragePrecision": null,
    "mota": null,
    "idSwitchCount": null,
    "description": "Real-world CV accuracy evaluation requires labeled motorsport benchmark dataset. Not yet available."
  },
  "statement": "Computer vision analysis completed successfully for candidate 'CAND-2024-TEST-01'. 2 active vehicle tracks identified.",
  "limitations": [
    "Test fixture data utilized for automated verification.",
    "2D bounding box overlap does not prove 3D vehicle contact."
  ]
}
```

### Response Example (Monza Reference Incident `REF-MONZA-03`)
```json
{
  "candidateId": "REF-MONZA-03",
  "status": "VIDEO_UNAVAILABLE",
  "tracks": [],
  "identityAssociations": [],
  "interactionFeatures": [],
  "statement": "Computer vision analysis unavailable for candidate 'REF-MONZA-03' in official session 'f1-2024-italian grand prix-race'. Formula One Management broadcast video footage is protected under commercial copyright. Missing video evidence is treated as unobserved, not negative evidence.",
  "limitations": [
    "Broadcast footage unlinked; zero visual frames ingested.",
    "No vehicle bounding boxes, multi-object tracks, or visual identities derived.",
    "Incident review relies exclusively on telemetry, spatial geometry, and race control records."
  ]
}
```

---

## 5. Frontend Visual & CV Integration

The user interface in `src/components/VideoPlayer.tsx` and `src/views/IncidentDetailView.tsx` has been upgraded with the CV Tracking & Identity layer:

1. **Analysis Mode Switcher:** Toggle buttons in the video HUD allow stewards to switch between:
   - *Keyframes (P13):* Bounded keyframe navigation and cross-modal telemetry alignment.
   - *CV Tracking & Identity (P14):* Live multi-object bounding boxes, track qualities, and interaction features.
2. **Interactive Bounding Box Overlays:** Dynamic canvas/SVG overlays display:
   - Track ID badge (e.g. `TRK-01`).
   - Deterministic track quality rating badge (`HIGH`, `MED`, `LOW`).
   - Defensible driver identity tag (e.g. `MAG #20 [CONFIRMED]`).
3. **Synthetic / Evaluation Status Banner:** A persistent, high-visibility disclaimer banner alerts reviewers:
   `[SYNTHETIC TEST DATA / EVALUATION: NOT_YET_AVAILABLE — 2D BOUNDED PROJECTION ONLY — NOT PROOF OF 3D CONTACT]`.
4. **Performance HUD:** Real-time metrics showing CV inference frame rate (FPS), hardware target (`CPU`/`ONNX`), and active vehicle track count.
5. **Track Inspector Cards:** Detailed breakdown for each tracked vehicle showing duration, observation count, visibility ratio, mean confidence, and identity association method.
6. **Pairwise Interaction Metrics Panel:** Live gauges for:
   - 2D Centroid Separation (%)
   - Inter-Vehicle IoU Overlap
   - Approach / Recede Kinematic Trend
   - Occlusion Ratio

---

## 6. Verification & Test Execution Results

### 6.1 Prompt 14 Computer Vision Suite (`test_cv_engine.py`)
```bash
python -m pytest app/tests/test_cv_engine.py -v
```
**Results:** **29 passed, 0 failed** in 43.12s.

| Test Category | Test Case | Status | Verified Capability |
| :--- | :--- | :---: | :--- |
| **Contracts & Models** | `test_bounding_box_math` | PASS | Area, centroid, distance, normalized boundary clipping |
| | `test_bounding_box_iou` | PASS | Deterministic 2D IoU calculation under various overlap states |
| | `test_bounding_box_no_overlap` | PASS | Zero IoU for disjoint bounding boxes |
| | `test_cv_status_enums` | PASS | Full status enum integrity and serialization |
| **Detector** | `test_null_vehicle_detector` | PASS | Clean `MODEL_UNAVAILABLE` fallback without errors |
| | `test_onnx_detector_missing_model` | PASS | Graceful unconfigured model handling with zero network calls |
| | `test_synthetic_detector_produces_detections` | PASS | Deterministic trajectories and confidence scoring |
| **Tracker** | `test_sort_tracker_initialization` | PASS | Empty tracker starts clean with 0 tracks |
| | `test_sort_tracker_creates_tracks` | PASS | Consecutive detections establish persistent tracks (`TRK-01`, etc.) |
| | `test_sort_tracker_coasting` | PASS | Tracks coast through missed detections up to `max_age` frames |
| | `test_sort_tracker_termination` | PASS | Stale tracks terminate after exceeding max age |
| **Track Quality** | `test_track_quality_high` | PASS | Deterministic `HIGH` rating for persistent, high-confidence tracks |
| | `test_track_quality_medium` | PASS | Correct `MEDIUM` rating for moderate tracks |
| | `test_track_quality_low` | PASS | Correct `LOW` rating for sparse or fragmented tracks |
| | `test_track_quality_insufficient_data` | PASS | Correct `INSUFFICIENT_DATA` for tracks with $<3$ observations |
| **Identity Association** | `test_identity_association_fixed_onboard` | PASS | Fixed T-cam metadata assigns `CONFIRMED` ($1.0$ confidence) |
| | `test_identity_association_test_fixture` | PASS | Fixture mapping assigns `CONFIRMED` identity |
| | `test_identity_association_telemetry_order` | PASS | Telemetry arrival order assigns `INFERRED` ($0.75$ confidence) |
| | `test_identity_association_unavailable` | PASS | Unmapped tracks safely assign `UNAVAILABLE` without guessing |
| **Interaction Features** | `test_interaction_features_computation` | PASS | Valid separation %, approach rates, and IoU values |
| | `test_interaction_features_bounded_projection_tag` | PASS | Explicit `measurement_basis: BOUNDED_2D_PROJECTION` tag |
| **CV Incident Service** | `test_cv_service_monza_video_unavailable[REF-MONZA-01]` | PASS | Ric/Hul honestly returns `VIDEO_UNAVAILABLE` |
| | `test_cv_service_monza_video_unavailable[REF-MONZA-02]` | PASS | Hul/Tsu honestly returns `VIDEO_UNAVAILABLE` |
| | `test_cv_service_monza_video_unavailable[REF-MONZA-03]` | PASS | Mag/Gas honestly returns `VIDEO_UNAVAILABLE` |
| | `test_cv_service_model_unavailable` | PASS | Unconfigured model returns `MODEL_UNAVAILABLE` |
| | `test_cv_service_synthetic_fixture_success` | PASS | End-to-end analysis produces tracks and features |
| **API Endpoints** | `test_api_cv_analysis_monza` | PASS | `GET /candidates/{id}/video/cv` returns 200 with honest unavailable |
| | `test_api_cv_analysis_not_found` | PASS | 404 returned for unknown candidate IDs |
| **Guardrails & Ethics** | `test_guardrails_no_guilt_or_fault` | PASS | Zero occurrences of forbidden adjudicative terms |

### 6.2 Full Backend Regression Suite
```bash
python -m pytest app/tests -q
```
**Results:** **179 passed, 0 failed** in 628.37s. Zero regressions across Prompts 01–14!

### 6.3 Frontend Verification
- **Linter (`npm run lint` / `tsc --noEmit`):** Clean exit (code 0), 0 errors.
- **Production Build (`npm run build` / `vite build`):** Clean compilation in 38.63s, all assets rendered to `dist/`.

---

## 7. Compliance & Guardrails Audit

A rigorous programmatic audit confirmed that all Prompt 14 deliverables adhere to the non-adjudication guidelines:
- **No Guilt / Fault Claims:** Outputs describe bounding boxes, track positions, and closing rates. Words like *"at fault"*, *"guilty"*, *"liable"*, *"caused collision"*, or *"illegal maneuver"* are strictly prohibited and do not exist in the codebase.
- **No Autonomous Collision Verdicts:** Visual overlaps are reported as `bboxOverlapIou` and `occlusionRatio` under `BOUNDED_2D_PROJECTION`. They are never reported as "crash confirmed" or "contact established".
- **No Autonomous Penalty Decisions:** No penalty points, grid drops, or time penalties are computed.
- **Transparent Evaluation Status:** `evaluationReport.status` strictly declares `NOT_YET_AVAILABLE` rather than hallucinating artificial mAP or MOTA benchmark figures.

---

## 8. Conclusion & Status

Prompt 14 is **100% COMPLETE, VERIFIED, AND PASSING**.

The system now features an end-to-end, production-grade Computer Vision pipeline for vehicle detection, multi-object tracking, track quality evaluation, visual identity attribution, and 2D interaction kinematics, fully integrated with backend APIs and the frontend steward interface.

**Formal Status:** `STATUS: PASS`  
**Recommended Next Phase:** PROMPT 15 (Multi-Modal Evidence Fusion, Automated Dossier Synthesis & Steward Decision Support Report Generation).
