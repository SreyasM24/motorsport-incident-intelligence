# Computer Vision Dataset Specification & Ground Truth Protocol
Motorsport Incident Intelligence (MII)

## 1. Dataset Status & Discovery Finding

```yaml
REAL_VIDEO_STATUS: NOT_AVAILABLE
SYNTHETIC_FIXTURE_STATUS: AVAILABLE
DATASET_STATE_CLASSIFICATION: SYNTHETIC_VALIDATION_ONLY
```

### Real Motorsport Video Availability Audit
- **Official F1 Broadcast Footage:** Strictly unbundled and unlinked in this repository. All official Formula One broadcast video is commercially owned and copyrighted by Formula One Management (FOM) / Liberty Media and protected under international intellectual property laws.
- **Reference Case Policy (Monza 2024):** Official race reference cases (`REF-MONZA-01`, `REF-MONZA-02`, and `REF-MONZA-03`) maintain `status: VIDEO_UNAVAILABLE` with commercial copyright attribution. No unauthorized video streams or pirated footage are ingested or hosted.
- **Evaluation Status:** Because no peer-reviewed, publicly licensed, bounding-box-annotated Formula 1 multi-camera dataset is bundled, the system honestly reports:
  - `EVALUATION_STATUS: INSUFFICIENT_DATA` (or `NOT_YET_AVAILABLE` for real-world benchmark metrics).
  - No synthetic metric is ever passed off as real-world detection or tracking accuracy.

### Documented Public Motorsport & Automotive Datasets
For future integration of authorized or open research datasets, the following public benchmarks are cataloged:

| Dataset | Source / Maintainer | Domain | License | Annotations | Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F1TENTH Autonomous Racing** | University of Pennsylvania / F1TENTH Consortium | 1:10 Autonomous Racing Vehicles | MIT / Open Access | 2D LiDAR, Depth, Vehicle Odometry | Scale model vehicles, indoor tracks, no full-size F1 dynamics |
| **Roborace / Indy Autonomous Challenge** | IAC / Energy Systems Network | Full-Scale Autonomous Open-Wheel (Dallara AV-21) | Academic / Research Restricted | Multi-Camera, LiDAR, Telemetry | Non-contact racing doctrine; autonomous control, not FIA steward review |
| **Boxy Vehicle Dataset** | Bosch Center for AI / TU Munich | Highway Vehicle 3D/2D Bounding Boxes | CC BY-NC-SA 4.0 | 200k images, 2M vehicle bounding boxes | Passenger road vehicles; no single-seater motorsport aerodynamics or apex convergence |
| **UA-DETRAC** | University at Albany | Traffic Vehicle Multi-Object Tracking | CC BY 4.0 | 100k frames, 1.2M bounding boxes, tracking IDs | Static surveillance camera angles; urban road cars, low velocity |
| **BDD100K** | UC Berkeley | Driving Video Tracking & Detection | BSD-3-Clause | 100k videos, bounding boxes, MOT IDs | Dashcam perspective; street cars, non-racing kinematics |

---

## 2. Directory Layout

The `data/cv/` tree contains specifications, manifests, annotation schemas, and partition splits:

```
data/cv/
├── README.md                  # This specification and provenance document
├── manifest/
│   └── dataset_manifest.json  # Frame & video sample provenance manifest
├── annotations/
│   └── annotations_sample.json# Normalized & absolute bounding box ground truth annotations
└── splits/
    └── dataset_splits.json    # Leakage-safe group-based train/val/test splits
```

---

## 3. Coordinate System & Annotation Protocol

### Coordinate Systems
Bounding boxes support two explicit coordinate representations:
1. **`NORMALIZED_0_1` (Default):**
   - Coordinates $[x_{\min}, y_{\min}, x_{\max}, y_{\max}] \in [0.0, 1.0]^4$.
   - Origin $(0.0, 0.0)$ is at top-left; $(1.0, 1.0)$ is at bottom-right.
   - Normalized coordinates are resolution-invariant.
2. **`PIXEL_ABSOLUTE`:**
   - Integer coordinates $[x_{\min}, y_{\min}, x_{\max}, y_{\max}]$ or $[x, y, w, h]$ in pixels relative to frame dimensions $(W \times H)$.
- **Strict Rule:** Coordinate spaces must NEVER be mixed silently. Every annotation explicitly records its `coordinate_format`.

### Ground Truth vs Prediction Separation
- **`GROUND_TRUTH`:** Authoritative annotations from human annotators or certified fixture definitions.
- **`MODEL_PREDICTION`:** Output hypotheses emitted by a `VehicleDetector` or `VehicleTracker`.
- **`DERIVED_METRIC`:** Secondary computations (e.g. IoU overlap, centroid distance, approach rates).

Ground truth annotations must never be sourced from model outputs, tracker coasting, or telemetry proximity heuristics.

---

## 4. Group-Based Leakage-Safe Splits

To prevent severe temporal data leakage in video evaluation:
- **Rule:** Adjacent frames from the same video or camera sequence must **NEVER** be randomly partitioned across train and test sets.
- **Grouping Key:** Splits must be partitioned at the **Event**, **Session**, or **Video/Camera** group level (`group_key: session_id` or `source_video`).
