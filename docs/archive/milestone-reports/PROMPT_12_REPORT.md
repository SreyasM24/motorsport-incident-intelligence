# PROMPT 12 REPORT: VIDEO EVIDENCE INGESTION, TIME SYNCHRONIZATION & EVIDENCE ALIGNMENT

**Motorsport Incident Intelligence (MII) System**  
**Engineering Phase:** Prompt 12  
**Status:** **PASS** (Full Video Synchronization Framework & CV Readiness Verified)  
**Date:** September 2026  
**Artifact Path:** `docs/progress/PROMPT_12_REPORT.md`

---

## 1. Executive Summary

Prompt 12 introduces a mathematically rigorous, multi-camera **Video Evidence Ingestion and Time Synchronization Layer** to the Motorsport Incident Intelligence platform. 

Video evidence is designed to temporally align with:
- FastF1 25Hz CAN-bus telemetry
- Incident candidate milestones (`event_start`, `event_peak`, `event_end`)
- Chronological race control messages
- Reference-lap trajectory deviations and cornering overtake geometry

### Core Jurisprudential & Compliance Guardrails (Strictly Preserved)
1. **Zero Automated Fault Determination:** Video evidence presents factual synchronized playback windows and multi-camera perspectives for human steward investigation. Video evidence **never** determines guilt, sporting fault, or penalties.
2. **Zero Copyright Infringement:** The system does **not** store, download, or redistribute copyrighted broadcast footage (FOM / FIA property). It models verified timecode metadata, calibration correspondences, and synthetic local test fixtures.
3. **Zero Video Hallucination & Honest `VIDEO_UNAVAILABLE` Default:** If real video bytes are unlinked, the system explicitly reports `VIDEO_UNAVAILABLE` as a valid, non-penalizing state. No fake URLs or synthetic telemetry correlations are fabricated for broadcast footage.
4. **Orthogonal Multi-Modal Evidence:** Video evidence operates orthogonally to telemetry, baseline deviations, cornering geometry, race control notices, and ML candidate scores.
5. **Computer Vision Readiness Without Premature Detection:** Fully establishes the canonical `SynchronizedVideoFrame` contract for Prompt 13 without introducing premature YOLO, optical flow, or object detection models.

---

## 2. Existing Video Architecture Audit (Prior to Prompt 12)

Before Prompt 12 continuation:
- `backend/app/evidence/video_evidence.py` contained basic legacy placeholders: `VideoSyncStatus` enum, `VideoSourceMetadata`, `VideoClipRecommendation`, and `format_seconds_to_time`.
- `IncidentEvidenceDossier` mapped `video_evidence: VideoEvidenceSummary`, which defaulted to `VIDEO_UNAVAILABLE`.
- `src/components/VideoPlayer.tsx` checked `videoAvailable` boolean and rendered a static notice when false.
- There was no multi-point calibration solver, no multi-camera clock isolation, no quantified uncertainty bounds, no API endpoint for video synchronization, and no formal contract for downstream computer vision.

---

## 3. What Was Completed During Prompt 12

1. **Decoupled Pydantic Schemas (`backend/app/schemas/video_evidence.py`):**
   - Created dedicated schema module preventing circular imports between `app.schemas.incident` and `app.evidence.dossier`.
   - Defined enums: `VideoSyncStatus`, `VideoSourceType`, `SyncMethod`, `SyncConfidence`, `AnchorEventType`.
   - Defined core models: `VideoProvenanceRecord`, `CalibrationPoint`, `SynchronizationUncertainty`, `VideoTimeTransform`, `IncidentVideoWindow`, `CameraAlignmentInfo`, `SynchronizedVideoFrame`, `VideoEvidenceSummary`, `VideoEvidenceDetailResponse`.
2. **Deterministic Calibration & Transform Algorithms (`backend/app/evidence/video_evidence.py`):**
   - Implemented `VideoTimeTransform`: affine mapping $\text{video\_time} = a \times \text{session\_time} + b$ with exact inverse float recovery.
   - Implemented `compute_calibration_transform`:
     - Single-point ($N=1$): assumes unity scale factor ($a = 1.0$), solves offset $b$.
     - Multi-point ($N \ge 2$): computes least-squares regression for scale factor $a$ and offset $b$, clamping $a = 1.0$ if clock drift is $< 0.5\%$, and computes residual RMSE error.
     - Quantified uncertainty: assigns realistic error bounds ($\pm 0.04$s for DIRECT_TIMESTAMP, $\pm 0.20$s for MANUAL_CALIBRATION, $\pm 0.50$s for EVENT_ANCHOR).
3. **Multi-Camera Synchronization Service (`backend/app/services/video_service.py`):**
   - Implemented `VideoSynchronizationService` managing multiple independent camera feeds per candidate.
   - Preserves independent clocks, frame rates (e.g. 50 fps broadcast vs 25 fps onboard vs 30 fps trackside), offsets, and provenance records.
   - Integrated Monza 2024 reference cases (`REF-MONZA-01`, `REF-MONZA-02`, `REF-MONZA-03`) with honest `VIDEO_UNAVAILABLE` provenance.
   - Provided isolated `TEST_FIXTURE` multi-camera scenario for automated synchronization verification.
4. **REST API Endpoints (`backend/app/api/analysis.py`):**
   - Added `GET /api/v1/analysis/candidates/{candidate_id}/video`: Returns `VideoEvidenceSummary`.
   - Added `GET /api/v1/analysis/candidates/{candidate_id}/video/synchronization`: Returns detailed mathematical transform, calibration points, and uncertainty.
5. **Frontend Enhancement (`src/components/VideoPlayer.tsx` & `src/lib/types.ts`):**
   - Updated TypeScript contracts in `src/lib/types.ts`.
   - Enhanced `VideoPlayer.tsx` to dynamically display the honest unavailable reason, camera angle badges, and synchronization metadata without altering the existing layout or dark racing theme.
6. **Comprehensive Automated Test Suite (`backend/app/tests/test_video_evidence.py`):**
   - 17 test cases covering all 15 required validation points, CV readiness contract, and REST API endpoints.

---

## 4. Video Source & Time Alignment Architecture

### Temporal Mapping Formulation
$$\text{video\_time} = a \cdot \text{session\_time} + b$$
$$\text{session\_time} = \frac{\text{video\_time} - b}{a}$$
$$\text{frame\_number} = \lfloor \text{video\_time} \cdot \text{frame\_rate} \rceil$$

Where:
- $a$ is the time dilation / clock drift scaling factor ($a = 1.0$ for real-time video).
- $b$ is the additive temporal offset in seconds.
- $\text{session\_time}$ is the elapsed session telemetry time from the FastF1 canonical grid.

### Synchronization Methods & Calibrated Uncertainty
| Synchronization Method | Physical Basis | Nominal Accuracy ($\pm \epsilon$) | Confidence Rating |
|---|---|---|---|
| `DIRECT_TIMESTAMP` | Embedded SMPTE LTC / IRIG / NTP network timecode | $\pm 0.04$s (1 frame @ 25Hz) | **HIGH** |
| `MANUAL_CALIBRATION` | Human steward keyframe alignment (apex / contact point) | $\pm 0.10$s to $\pm 0.20$s | **MEDIUM** |
| `EVENT_ANCHOR` | Physical event correlation (lights out, transponder loop) | $\pm 0.30$s to $\pm 0.50$s | **MEDIUM** |
| `UNKNOWN` | Unsynchronized / unlinked video | N/A | **NONE** |

> [!IMPORTANT]
> **Anti-False Precision Guarantee:** The system forbids claiming false precision (such as $\pm 0.001$s) when synchronization is derived from visual or transponder event anchors. Error bounds reflect physical measurement constraints.

---

## 5. Multi-Camera Support

In real motorsport investigations, multiple cameras capture an incident from distinct angles with different clock sources:
1. **World Feed Broadcast (Main Feed):** Typical 50.0 fps (1080p50), fixed broadcast delay offset.
2. **Car A Onboard Camera:** Typical 25.0 fps, roll-hoop or nose-cone angle, synchronized via car ECU dash display.
3. **Car B Onboard Camera:** Independent wireless broadcast transmitter, independent frame drop characteristics.
4. **Trackside Marshal / CCTV:** Typical 30.0 fps, localized sector time.

`VideoSynchronizationService` processes each camera feed independently via `CameraAlignmentInfo`, calculating camera-specific incident clip boundaries:
- `video_start = session_to_video(t_start - pre_roll)`
- `video_peak = session_to_video(t_peak)`
- `video_end = session_to_video(t_end + post_roll)`

---

## 6. Computer Vision Readiness Contract (Prompt 13 Handoff)

Prompt 12 establishes the strict `SynchronizedVideoFrame` contract for future downstream Computer Vision modules (Prompt 13):

```python
class SynchronizedVideoFrame(BaseModel):
    video_id: str                      # Camera feed identifier
    camera: str                        # E.g. 'World Feed Broadcast' or 'Car 20 Onboard'
    video_timestamp: str               # '00:00:15.000' (playback timecode)
    video_time_sec: float              # 15.000
    session_timestamp: str             # '2024-09-01 13:04:15.000' (telemetry UTC)
    session_time_sec: float            # 15.000
    frame_number: Optional[int]        # 750 (at 50 fps)
    synchronization_error_sec: float   # +/- 0.04s
    provenance: Optional[VideoProvenanceRecord]
```

This ensures Prompt 13 can consume aligned frame sequences directly without having to recalculate timecodes or assume synchronous clocks.

---

## 7. Real-Data Validation (Monza 2024) & Synthetic Test Fixture

### Monza 2024 Official Reference Cases
| Candidate | Incident Description | Video Availability | Justification & Provenance |
|---|---|---|---|
| `REF-MONZA-01` | Ricciardo vs Hülkenberg (Lap 1, Ascari) | `VIDEO_UNAVAILABLE` | FOM broadcast rights reserved. Metadata recorded; video unlinked. |
| `REF-MONZA-02` | Hülkenberg vs Tsunoda (Lap 4, Prima Variante) | `VIDEO_UNAVAILABLE` | FOM broadcast rights reserved. Metadata recorded; video unlinked. |
| `REF-MONZA-03` | Magnussen vs Gasly (Lap 19, Variante della Roggia) | `VIDEO_UNAVAILABLE` | FOM broadcast rights reserved. Metadata recorded; video unlinked. |

### Automated Test Fixture (`TEST_FIXTURE`)
A synthetic 3-camera setup is registered under `TEST_FIXTURE` with known ground truth timestamps to comprehensively validate:
- 50 fps World Feed with $+10.0$s offset
- 25 fps Car 20 Onboard with zero offset (ECU synchronized)
- 30 fps Trackside CCTV with affine scale dilation ($a = 1.002$)

---

## 8. Verification Results

| Suite / Verification Step | Command | Result | Status |
|---|---|---|---|
| **Prompt 12 Video Evidence Tests** | `pytest app/tests/test_video_evidence.py -v` | **17 passed, 0 failed** | **PASS** |
| **Full Backend Regression Suite** | `pytest app/tests -q` | **133 passed, 0 failed** | **PASS** |
| **Frontend TypeScript Typecheck** | `npx tsc --noEmit` | **0 errors** | **PASS** |
| **Frontend Production Build** | `npm run build` (`vite build`) | **Successful** (845 kB JS, 76 kB CSS) | **PASS** |

### Historical Regression Audit
- Prompts 01–06 (Reconstruction, Telemetry, Persistence, Dossier): **All tests pass**
- Prompt 07 (Persistence & Review Workflow): **All tests pass**
- Prompt 08 (Reference-Lap Baseline): **All tests pass**
- Prompt 09 (Overtake Geometry & Apex Overlap): **All tests pass**
- Prompt 10 & 11 (ML Readiness & Multi-Circuit Validation): **All tests pass**
- Prompt 12 (Video Evidence & Synchronization): **All tests pass**

---

## 9. Final Acceptance

```
STATUS: PASS
```

All 21 sections of Prompt 12 have been implemented and validated:
- Video source abstraction and metadata quality tracking implemented.
- Affine time transform ($a \cdot t + b$) with least-squares calibration and RMSE uncertainty implemented.
- Multi-camera alignment architecture implemented.
- Honest `VIDEO_UNAVAILABLE` default preserved with zero fabricated URLs or footage.
- REST API endpoints (`/video` and `/video/synchronization`) live and tested.
- Frontend displays dynamic camera labels and honest unlinked notices without layout alterations.
- 133/133 backend tests passing.
- 0 TypeScript errors; production build clean.

---

### RECOMMENDED PROMPT 13

**Prompt 13: Bounded Visual Evidence Feature Extraction & Multi-Modal Alignment**

With the temporal synchronization layer certified:
1. **Visual Bounding & Region of Interest (ROI) Extraction:** Define track-coordinate to video-frame projection matrices where camera calibration parameters are known.
2. **Optical Apex & Contact Keyframe Annotation:** Allow stewards to review frame sequences corresponding to the $\pm 2.0$s window around telemetry peak closing speed.
3. **Multi-Modal Verification Check:** Cross-validate whether the video-observed apex moment aligns within the telemetry minimum distance window ($\pm \epsilon_{\text{sync}}$).
4. **Preserve Non-Goal Guardrails:** Continue strictly prohibiting autonomous fault assignment or automated contact verdict from pixels alone.
