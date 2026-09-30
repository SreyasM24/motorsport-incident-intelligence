# Dataset Card: Motorsport Video & Computer Vision Evaluation Dataset (MII-CV)

**Version:** 2.0  
**Status:** `REAL_WORLD_VIDEO_STATUS = INSUFFICIENT_DATA`  
**License Policy:** Strict Copyright Compliance & Open Research Consortium  
**Manifest Path:** `data/cv/real_video_manifest.json`  

---

## 1. Dataset Summary

The **Motorsport Video & Computer Vision Evaluation Dataset (MII-CV)** provides a rigorous evaluation foundation for multi-object vehicle detection, tracking, temporal synchronization, and cross-modal evidence synthesis in competitive motorsport environments.

### Core Epistemic & Legal Reality
- **Commercial Copyright Restriction:** Formula One Management (FOM) broadcast footage, trackside CCTV, and onboard camera feeds are proprietary commercial assets owned by Formula One Licensing B.V. and Liberty Media. **Zero raw commercial broadcast frames are bundled, scraped, or committed to this open repository.**
- **Honest Status Reporting:** The system explicitly reports `REAL_WORLD_VIDEO_STATUS = INSUFFICIENT_DATA` (and `real_video_status = NOT_AVAILABLE`) rather than claiming false real-world accuracy or deceptively substituting synthetic data.
- **Evaluation Scope:** Quantitative metric benchmarks are derived from certified open research datasets (e.g., F1TENTH Autonomous Racing, Indy Autonomous Challenge, UA-DETRAC) and mathematically verified deterministic synthetic simulation fixtures.

---

## 2. Dataset Architecture & Manifest Specification

All video assets and metadata records are cataloged in `data/cv/real_video_manifest.json` under the following schema:

| Field | Type | Description |
| :--- | :--- | :--- |
| `videoId` | `string` | Unique identifier (e.g. `VID-RESEARCH-F1TENTH-PENN-01`) |
| `series` | `string` | Racing series (e.g. `Formula 1`, `F1TENTH`, `Indy Autonomous Challenge`) |
| `season` | `integer` | Calendar year |
| `event` | `string` | Grand Prix or competition venue name |
| `session` | `string` | Session code (`RACE`, `QUALIFYING`, `PASSING_COMPETITION`) |
| `cameraId` | `string` | Physical camera mount or broadcast feed ID |
| `sourceType` | `enum` | `BROADCAST_WORLD_FEED`, `ONBOARD_CAMERA`, `TRACKSIDE_CCTV`, `AUTHORIZED_RESEARCH_DATASET`, `SYNTHETIC_SIMULATION` |
| `sourceUrl` | `string` | Canonical reference, documentation, or DOI link |
| `licenseStatus` | `string` | Legal license (`COMMERCIAL_RESTRICTED_FOM`, `CC_BY_4_0`, `APACHE_2_0`, `MIT`) |
| `authorizationStatus` | `enum` | `AVAILABLE`, `AUTHORIZED`, `UNAUTHORIZED`, `PENDING_REVIEW`, `UNAVAILABLE`, `SYNTHETIC` |
| `durationSeconds` | `float` | Clip duration in seconds |
| `frameRate` | `float` | Frame rate (e.g. `25.0`, `30.0`, `50.0`) |
| `resolution` | `string` | Spatial resolution (e.g. `1920x1080`, `1280x720`) |
| `timestampReference` | `string` | Timecode basis (`SESSION_ELAPSED_SEC`, `ROS_CLOCK_UTC`, `GPS_TIME_UTC`) |
| `timezone` | `string` | Local venue timezone |
| `incidentCaseIds` | `list[str]` | Cross-reference to benchmark candidate incidents |
| `annotationStatus` | `string` | Ground truth annotation level (`COMPLETE`, `PARTIAL`, `UNANNOTATED`, `SYNTHETIC_GROUND_TRUTH`) |
| `split` | `string` | Partition assignment (`TRAIN`, `VAL`, `TEST`, `BENCHMARK_EVAL`) |
| `provenance` | `string` | Authoritative source provenance description |
| `contentHash` | `string` | SHA-256 cryptographic digest of media file |

### Strict Authorization Invariant
```
UNAUTHORIZED is NEVER treated as AVAILABLE or AUTHORIZED.
Unauthorized stream captures or unverified third-party rips are strictly quarantined
and excluded from evaluation suites and deployment pipelines.
```

---

## 3. Annotation Schema & Validation Protocol

Annotations are stored with explicit coordinate formatting and full provenance lineage:

### Coordinate Formats
1. **`NORMALIZED_0_1`**: Bounding box normalized coordinates `[x_min, y_min, x_max, y_max]` where all coordinates strictly satisfy $0.0 \le c \le 1.0$ and $x_{min} < x_{max}$, $y_{min} < y_{max}$.
2. **`PIXEL_ABSOLUTE`**: Integer pixel coordinates `{"x": int, "y": int, "w": int, "h": int}` bounded by frame width and height.

### Quality Validation Rules
- **Boundary Clamping:** Conversions between normalized and pixel coordinates strictly enforce clipping to `[0, frame_dimension - 1]`.
- **Visibility & Occlusion:** Occlusion and truncation metrics are bounded in $[0.0, 1.0]$.
- **Sequence Monotonicity:** Frame timestamps for track sequences must be strictly non-decreasing.
- **Track ID Uniqueness:** Duplicate track IDs in the same frame trigger a hard validation error.

---

## 4. Group-Aware Splitting (LOVO & LOEO)

To prevent temporal and environmental data leakage:
- **Leave-One-Video-Out (LOVO):** Holds out entire video sequences as the test set. Frames from the same video feed are never partitioned across training and testing sets.
- **Leave-One-Event-Out (LOEO):** Holds out entire racing circuits or grand prix events. Prevents background track landmarks, curb colors, and lighting conditions from leaking into model evaluation.
- **Zero-Leakage Invariant:** Validated at runtime by intersecting the set of video and event identifiers across partitions.

---

## 5. 12-Category Computer Vision Failure Taxonomy

Evaluation failures are classified into 12 mutually exclusive primary failure categories:

1. **`DETECTION_MISS`**: Vehicle present in ground truth but unpredicted by the detector ($IoU < \tau$).
2. **`FALSE_DETECTION`**: Detector prediction with no corresponding ground truth vehicle (hallucination or debris).
3. **`OCCLUSION`**: Detection failure caused by another vehicle, trackside barrier, or dust cloud obscuring $>40\%$ of the vehicle.
4. **`TRUNCATION`**: Detection failure at frame boundaries where the vehicle is partially out of frame.
5. **`TRACK_FRAGMENTATION`**: A continuous ground truth track is split into multiple predicted track IDs.
6. **`ID_SWITCH`**: A predicted track swaps identity between two distinct interacting vehicles.
7. **`IDENTITY_UNAVAILABLE`**: Driver identity attribution is missing or uncertain due to lack of optical livery/helmet annotations.
8. **`TIMESTAMP_MISALIGNMENT`**: Discrepancy between visual timecodes and telemetry event timestamps ($|\Delta t| > \tau_{sync}$).
9. **`CAMERA_GEOMETRY`**: Severe lens distortion, extreme oblique perspective, or non-stereoscopic monocular depth ambiguity.
10. **`INSUFFICIENT_RESOLUTION`**: Vehicle bounding box area $< 0.01$ of frame area, preventing reliable feature extraction.
11. **`VIDEO_UNAVAILABLE`**: Video stream unlinked or absent due to commercial licensing restrictions (`VIDEO_EVIDENCE_UNAVAILABLE`).
12. **`OTHER`**: Environmental anomalies, extreme lens glare, or broadcast telemetry graphics overlay occlusion.

---

## 6. Independent Identity Attribution

- **Rule:** Driver identity attribution requires authoritative camera telemetry, helmet designs, or high-resolution car livery numbers.
- **Enforcement:** If independent ground truth identity annotations are not present, the system MUST report `IDENTITY_EVALUATION = INSUFFICIENT_DATA`.
- **Guardrail:** The system NEVER claims 100% identity accuracy based on synthetic labels or telemetry-derived driver mappings.

---

## 7. Cross-Modal Validation & Non-Adjudication Philosophy

### Discrepancy Interpretation
Any spatial discrepancy between visual bounding boxes (2D perspective projection) and telemetry position traces (2D track coordinates) or temporal delta $|\Delta t|$ is cataloged as an **evidence-quality flag**:
- Indicates sensor alignment uncertainty, broadcast transmission delay, or optical perspective distortion.
- **NEVER** constitutes driver fault, steering illegality, or sporting guilt.

### Steward Decision Support
Visual evidence is classified into three distinct epistemic types:
- **`OBSERVED / GROUND_TRUTH`**: Human steward annotations or verified raw camera feeds.
- **`MODEL_DERIVED`**: Computer vision bounding boxes, optical flow, and multi-object tracker trajectories.
- **`DERIVED`**: Calculated kinematic interactions, time-to-contact, and lateral closing velocities.

When video footage is absent, the system outputs `VIDEO_EVIDENCE_UNAVAILABLE` and defers to high-frequency CAN-bus telemetry, reference-lap analysis, and official FIA race control documentation.
