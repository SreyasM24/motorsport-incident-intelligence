# PROMPT 13 — BOUNDED VISUAL EVIDENCE FEATURE EXTRACTION & MULTI-MODAL ALIGNMENT REPORT

**Date:** 2026-09-28  
**Status:** COMPLETE & VERIFIED  
**Backend Suite:** 150 passed, 0 failed (100% passing)  
**Prompt 13 Visual Suite:** 17 passed, 0 failed  
**Frontend TypeScript:** 0 errors (`npx tsc --noEmit` clean)  
**Frontend Production Build:** Built in 12.15s (`npm run build` clean)  

---

## 1. Executive Summary

Prompt 13 adds a **Bounded Visual Evidence & Multi-Modal Alignment** layer on top of the verified time-synchronization foundation established in Prompt 12. The module extracts frame-accurate keyframes, computes mathematically defensible 2D image-plane metrics (Regions of Interest, vehicle bounding boxes, centroids, Intersection-over-Union, image-plane separation, approach/recede trends, and occlusion flags), and conducts deterministic cross-modal checks between visual minimum separation and telemetry peak proximity.

### Strict Jurisprudential & Compliance Doctrine
1. **Zero Autonomous Guilt or Fault Determination:** Visual features (IoU, centroid proximity, bounding boxes) are strictly descriptive 2D geometric and kinematic measurements. They NEVER decide fault, driver blame, sporting legality, or collision contact verdicts.
2. **Zero Copyright Infringement & Zero Video Fabrication:** No copyrighted FOM or FIA broadcast footage is stored, streamed, or redistributed.
3. **Honest `UNAVAILABLE` Default for Real Grand Prix Sessions:** For the official 2024 Italian Grand Prix reference cases (`REF-MONZA-01`, `REF-MONZA-02`, and `REF-MONZA-03`), the system honestly reports `status: UNAVAILABLE` with explicit commercial copyright attribution. Missing visual footage is treated as missing evidence, never as negative evidence.
4. **Strict `TEST_FIXTURE` Isolation:** Automated tests use explicitly labeled `TEST_FIXTURE` metadata with SMPTE/LTC timecode calibrations to test keyframe extraction, 2D IoU overlap, and cross-modal alignment without fabricating real race footage.
5. **Perspective Projection vs. 3D Reality:** All visual features carry an explicit `measurement_basis: "BOUNDED_2D_PROJECTION"` flag, affirming that 2D image-plane coordinates represent perspective projections and do not assert 3D world contact without full 3D camera calibration.

---

## 2. Visual Evidence Architecture

The visual evidence system is decoupled into the dedicated `backend/app/evidence/visual/` package:

```
backend/app/evidence/visual/
├── __init__.py           # Package exports & public API
├── models.py             # Pydantic data models & status contracts
├── extractor.py          # Frame-accurate keyframe & bounded 2D feature extractor
└── service.py            # VisualEvidenceService orchestrating multi-modal checks
```

And mirrored in schemas for API contracts:
- `backend/app/schemas/visual_evidence.py`
- Re-exported in `backend/app/schemas/video_evidence.py` and `backend/app/evidence/dossier.py`

### 2.1 Core Data Models (`models.py`)

- **`VisualObservationStatus`**: Enum (`OBSERVED`, `DERIVED`, `UNAVAILABLE`).
- **`DriverAssociationStatus`**: Enum (`CONFIRMED`, `INFERRED`, `UNAVAILABLE`).
- **`VisibilityState`**: Enum (`IN_FRAME`, `PARTIAL`, `OCCLUDED`, `OUT_OF_FRAME`).
- **`ApproachTrend`**: Enum (`APPROACHING`, `RECEDING`, `STABLE`, `UNKNOWN`).
- **`AlignmentStatus`**: Enum (`ALIGNED`, `PARTIALLY_ALIGNED`, `MISALIGNED`, `INSUFFICIENT_DATA`).
- **`VisualROI`**:
  - Normalized bounds $[x_{\min}, y_{\min}, x_{\max}, y_{\max}] \in [0, 1]^4$.
  - Optional pixel coordinates $\{x, y, w, h\}$.
  - Properties: `width`, `height`, `centroid`, `area`.
  - Deterministic 2D IoU method: `compute_iou(other: VisualROI) -> float`.
- **`VisualTrackObservation`**: Track ID, driver code, association status, centroid, bounding box, visibility, detection confidence, track persistence frame count.
- **`VisualFeatureEvidence`**:
  - `centroid_displacement_px`: Inter-frame displacement.
  - `bbox_width_norm`, `bbox_height_norm`: Normalized dimensions.
  - `bbox_overlap_iou`: 2D Intersection-over-Union.
  - `image_plane_separation_norm`: Normalized Euclidean distance between vehicle centroids.
  - `approach_recede_trend`: `APPROACHING` / `RECEDING` / `STABLE`.
  - `occlusion_detected` and `occlusion_ratio`: Overlap occlusion tracking.
  - `measurement_basis`: `"BOUNDED_2D_PROJECTION"`.
- **`VisualKeyframe`**:
  - Event-relative timestamp $\Delta t$ ($\pm 2.0$s around peak/apex: entry $-1.5$s, approach $-0.5$s, apex $0.0$s, exit $+1.0$s).
  - Synchronized video and session timestamps.
  - Frame index, camera ID, track observations, ROIs, features, synchronization error, and alignment status.
- **`CrossModalAlignment`**:
  - Telemetry event session seconds ($t_{\text{telemetry}}$).
  - Visual minimum image-plane separation session seconds ($t_{\text{visual}}$).
  - $\Delta t = t_{\text{visual}} - t_{\text{telemetry}}$.
  - Synchronization uncertainty ($\pm \sigma$) and tolerance ($\pm 0.20$s).
  - Deterministic status: `ALIGNED` ($|\Delta t| \le 0.20$s), `PARTIALLY_ALIGNED` ($|\Delta t| \le 0.20\text{s} + \sigma$), `MISALIGNED`, or `INSUFFICIENT_DATA`.
- **`VisualEvidenceQuality`**: Quality rating (`HIGH`, `MEDIUM`, `LOW`, `UNUSABLE`), FPS, resolution, occlusion frequency, sync uncertainty, track persistence.
- **`VisualEvidenceSummary`**: Master container integrated into `IncidentEvidenceDossier` and `VideoEvidenceSummary`.

---

## 3. Keyframe Extraction & Multi-Modal Alignment

### 3.1 Extraction Logic (`extractor.py`)
- Given an incident time window, samples key points relative to peak closing speed / apex:
  - $t = -1.5$s: Entry phase (cars entering frame, approaching, IoU = 0.0)
  - $t = -0.5$s: Pre-apex approach (closing proximity, IoU = 0.0)
  - $t = 0.0$s: Apex proximity (minimum separation, side-by-side overlap IoU > 0)
  - $t = +1.0$s: Exit separation (cars diverging, IoU = 0.0)
- Applies affine calibration transform ($t_{\text{video}} = a \cdot t_{\text{session}} + b$) from Prompt 12 to map session timestamps into frame-accurate video timecodes and integer frame indices.
- Computes deterministic IoU and centroid separation across frames.

### 3.2 Cross-Modal Telemetry-Visual Verification
The cross-modal check compares the physical minimum distance identified in 25Hz telemetry coordinates with the visual keyframe exhibiting minimum image-plane separation:
$$\Delta t = t_{\text{visual, min sep}} - t_{\text{telemetry, min gap}}$$
- If $|\Delta t| \le 0.20$s: `ALIGNED`
- If $0.20\text{s} < |\Delta t| \le 0.20\text{s} + \sigma_{\text{sync}}$: `PARTIALLY_ALIGNED`
- If $|\Delta t| > 0.20\text{s} + \sigma_{\text{sync}}$: `MISALIGNED`
- If video or visual features are absent: `INSUFFICIENT_DATA`

---

## 4. API Endpoints

A new dedicated visual evidence endpoint has been added to `backend/app/api/analysis.py`:

```http
GET /api/v1/analysis/candidates/{candidate_id}/video/visual-evidence
```

**Response Contract (`VisualEvidenceSummary`):**
```json
{
  "status": "OBSERVED",
  "cameraId": "FIXTURE-CAM-WF",
  "cameraLabel": "Test Broadcast World Feed",
  "keyframes": [
    {
      "keyframeId": "KF-FIXTURE-CAM-WF-98.5",
      "eventRelativeTimeSec": -1.5,
      "videoTimestamp": "00:01:48.500",
      "videoTimeSec": 108.5,
      "sessionTimestamp": "00:01:38.500",
      "sessionTimeSec": 98.5,
      "frameNumber": 5425,
      "cameraId": "FIXTURE-CAM-WF",
      "cameraLabel": "Test Broadcast World Feed",
      "observations": [...],
      "rois": [...],
      "features": {
        "featureSetId": "FEAT-FIXTURE-CAM-WF-5425",
        "centroidDisplacementPx": 14.2,
        "bboxWidthNorm": 0.12,
        "bboxHeightNorm": 0.08,
        "bboxOverlapIou": 0.0,
        "imagePlaneSeparationNorm": 0.171,
        "approachRecedeTrend": "APPROACHING",
        "trackPersistenceCount": 1,
        "occlusionDetected": false,
        "occlusionRatio": 0.0,
        "confidenceScore": 0.97,
        "measurementBasis": "BOUNDED_2D_PROJECTION"
      },
      "synchronizationErrorSec": 0.0,
      "alignmentStatus": "ALIGNED"
    }
  ],
  "trackObservations": [...],
  "crossModalAlignment": {
    "telemetryEventTimeSec": 100.0,
    "visualEventTimeSec": 100.0,
    "deltaSeconds": 0.0,
    "synchronizationUncertaintySec": 0.04,
    "toleranceSec": 0.20,
    "alignmentStatus": "ALIGNED",
    "description": "Visual image-plane closest point aligns with telemetry peak within +/-0.20s tolerance (observed delta: +0.000s)."
  },
  "quality": {
    "qualityRating": "HIGH",
    "frameRateFps": 50.0,
    "resolution": "1920x1080",
    "occlusionFrequency": 0.25,
    "syncUncertaintySec": 0.04,
    "averageTrackPersistence": 2.5,
    "notes": [...]
  },
  "statement": "Bounded visual evidence extracted from camera 'Test Broadcast World Feed' [TEST_FIXTURE]. 4 keyframes analyzed across incident window. Cross-modal alignment: ALIGNED (delta: +0.000s, tolerance: +/-0.20s).",
  "limitations": [
    "Visual observations represent 2D perspective projection onto the camera plane.",
    "2D image-plane overlap (IoU) and proximity do NOT establish 3D physical contact or fault.",
    "Human steward review is required for all sporting and regulatory assessments.",
    "Synchronization uncertainty: +/-0.04s via VIDEO_SYNCHRONIZED."
  ]
}
```

For Monza reference cases (`REF-MONZA-01`, `02`, `03`):
```json
{
  "status": "UNAVAILABLE",
  "cameraId": null,
  "cameraLabel": null,
  "keyframes": [],
  "trackObservations": [],
  "crossModalAlignment": {
    "telemetryEventTimeSec": 13.4,
    "visualEventTimeSec": null,
    "deltaSeconds": null,
    "alignmentStatus": "INSUFFICIENT_DATA",
    "description": "Official race broadcast footage unlinked due to commercial licensing. Cross-modal visual alignment cannot be evaluated."
  },
  "statement": "Visual evidence is unavailable and unlinked for candidate 'REF-MONZA-01' in official session 'f1-2024-italian grand prix-race'. Formula One Management broadcast footage is protected under commercial copyright. Missing visual evidence is treated as an honest unobserved state, not negative evidence.",
  "limitations": [
    "Broadcast footage unlinked; zero visual frames ingested.",
    "No visual ROIs, bounding boxes, or image-plane features derived.",
    "Incident evidence relies exclusively on telemetry, spatial baseline, and race control records."
  ]
}
```

---

## 5. Frontend Visual Evidence Integration

`src/components/VideoPlayer.tsx` has been enhanced with:
1. **Cross-Modal Alignment Badge:** Placed in the video HUD alongside camera provenance, displaying live synchronization status (`ALIGNED`, `PARTIALLY_ALIGNED`, `MISALIGNED`, or `INSUFFICIENT_DATA`) and $\Delta t$ delta offset.
2. **Interactive Bounding Box Overlays:** Optional dashed ROI bounding boxes with car identifiers (`CAR 1`, `CAR 2`) rendered directly on top of the video canvas with toggle control.
3. **Keyframe Navigation Strip:** 4 interactive cards displaying relative time, approach trend badge, 2D image separation percentage, and IoU overlap metric. Clicking a keyframe jumps playback to that moment.
4. **Steward Decision Support Disclaimer:** Clear footer affirming that 2D image-plane projections do not constitute 3D contact proof and require human steward assessment.

---

## 6. Verification & Test Execution Results

### 6.1 Prompt 13 Dedicated Test Suite (`test_visual_evidence.py`)
```bash
python -m pytest app/tests/test_visual_evidence.py -v
```
**Results:** **17 passed, 0 failed** in 47.89s.

| Test Case | Status | Verified Capability |
| :--- | :---: | :--- |
| `test_visual_observation_status_values` | PASS | Status enum integrity (`OBSERVED`, `DERIVED`, `UNAVAILABLE`) |
| `test_visual_roi_math_and_iou` | PASS | Bounding box area, centroid, and deterministic 2D IoU calculation |
| `test_visual_track_observation_contract` | PASS | Single-vehicle track observation contract and metadata |
| `test_keyframe_extractor_synthetic_fixture` | PASS | 4 keyframes around peak, correct relative times $[-1.5, -0.5, 0.0, 1.0]$ |
| `test_keyframe_extractor_unavailable_source` | PASS | Honest empty list returned for unlinked sources without fabrication |
| `test_cross_modal_alignment_aligned` | PASS | Synchronized minimum separation within tolerance $\implies$ `ALIGNED` |
| `test_cross_modal_alignment_partially_aligned` | PASS | Discrepancy within tolerance + uncertainty $\implies$ `PARTIALLY_ALIGNED` |
| `test_cross_modal_alignment_misaligned` | PASS | Discrepancy exceeding uncertainty $\implies$ `MISALIGNED` |
| `test_cross_modal_alignment_insufficient_data` | PASS | Missing visual keyframes $\implies$ `INSUFFICIENT_DATA` |
| `test_monza_reference_cases_honest_unavailable[REF-MONZA-01]` | PASS | Ric/Hul Lap 1 Ascari honestly reports `UNAVAILABLE` with copyright notice |
| `test_monza_reference_cases_honest_unavailable[REF-MONZA-02]` | PASS | Hul/Tsu Lap 4 T1 honestly reports `UNAVAILABLE` with copyright notice |
| `test_monza_reference_cases_honest_unavailable[REF-MONZA-03]` | PASS | Mag/Gas Lap 19 Roggia honestly reports `UNAVAILABLE` with copyright notice |
| `test_dossier_synthesis_includes_visual_evidence` | PASS | Master dossier synthesis attaches visual evidence & cross-modal fields |
| `test_convert_dossier_to_frontend_incident_with_visual_evidence` | PASS | Frontend conversion includes `VISUAL` assessment item and alignment status |
| `test_api_candidate_visual_evidence_monza` | PASS | `GET /candidates/{id}/video/visual-evidence` returns 200 with honest unavailable state |
| `test_api_candidate_visual_evidence_not_found` | PASS | 404 returned for unknown candidate IDs |
| `test_bounded_guardrails_no_guilt_or_fault` | PASS | Zero forbidden adjudicative terms ("guilty", "at fault", "penalty applied") |

### 6.2 Full Backend Regression Suite
```bash
python -m pytest app/tests -q
```
**Results:** **150 passed, 0 failed** in 568.85s (0 regressions against Prompts 01–12).

### 6.3 Frontend Verification
- `npm run lint` (`tsc --noEmit`): **0 errors**.
- `npm run build` (`vite build`): **Successful production build** in 12.15s.

---

## 7. Conclusion

Prompt 13 is complete. The system now possesses a rigorous, bounded visual evidence analysis layer that connects synchronized video playback with telemetry-anchored keyframes and cross-modal alignment verification, adhering strictly to steward-decision-support principles with zero automated guilt determination and transparent provenance reporting.
