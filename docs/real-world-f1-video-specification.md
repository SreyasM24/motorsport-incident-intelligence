# Real-World Formula 1 Broadcast Video Acquisition & Annotation Protocol Specification

**Document Version:** 1.0.0  
**Status:** Canonical Engineering & Epistemic Standard  
**Subsystem:** Computer Vision & Multi-Modal Incident Ingestion  
**Operational Status:** `REAL_WORLD_VIDEO_STATUS = INSUFFICIENT_DATA`  
**Related Documents:**
- [`docs/evaluation/video_cv_evaluation.md`](video_cv_evaluation.md)
- [`data/cv/DATASET_CARD.md`](../data/cv/DATASET_CARD.md)
- [`data/cv/real_video_manifest.json`](../data/cv/real_video_manifest.json)

---

## 1. Executive Summary & Epistemic Invariants

### 1.1 The Operational Status
The Motorsport Incident Intelligence (MII) system maintains an explicit and transparent operational boundary:
```json
{
  "realWorldVideoStatus": "INSUFFICIENT_DATA",
  "reason": "Commercial FOM broadcast footage is legally restricted under proprietary copyright. Zero unauthorized video frames are committed, scraped, or bundled."
}
```
MII rejects the fabrication of synthetic accuracy metrics disguised as real-world broadcast performance. When operating without an active commercial broadcasting partnership, the system honestly reports visual evidence as unbundled or unavailable, relying on telemetry and sporting data as primary empirical baselines.

### 1.2 The Non-Adjudicative Epistemic Doctrine
Under all circumstances and across all future integrations:
1. **Descriptive Support Only:** Computer vision algorithms provide descriptive spatial and temporal evidence (vehicle bounding boxes, proximity measurements, track limits position, contact timestamps) to assist human race stewards.
2. **Zero Autonomous Fault Attribution:** The system **never** attributes fault, assigns blame, or calculates driver liability percentages from video feeds.
3. **Zero Autonomous Penalty Determination:** The system **never** recommends, predicts, or enforces sporting penalties, fines, or grid drops.
4. **Discrepancies Indicate Sensor Uncertainty:** Offsets between visual detections and telemetry events are flagged as epistemic discrepancies for human evaluation, **not** as evidence of driver misconduct.

---

## 2. Legal Acquisition & Secure Ingest Architecture

For sanctioned deployments (e.g., by the Fédération Internationale de l'Automobile (FIA), Formula One Management (FOM), or authorized racing teams), video data must be acquired strictly through authorized, low-latency, broadcast-grade ingest streams.

### 2.1 Authorized Broadcast Ingest Feeds
| Stream Type | Protocol / Format | Resolution & Frame Rate | Timecode Synchronization |
| :--- | :--- | :--- | :--- |
| **World Feed (Program)** | SMPTE ST 2110-20 / SRT / SDI | 1080p50 or 4K UHD 50/59.94 fps | SMPTE 12M Linear Timecode (LTC) |
| **Onboard Feeds (Driver A & B)** | H.265 (HEVC) Low-Latency SRT | 1080p50 | Embedded Ancillary Timecode (ATC) |
| **Trackside Marshaling CCTV** | RTSP / WebRTC (H.264/H.265) | 1080p30 / 1080p50 | PTP (IEEE 1588) synchronized UTC |
| **High-Speed Apex Cameras** | Uncompressed SDI / Raw Stream | 1080p200+ | Hardware Genlock / GPS PTP |

### 2.2 Security & Compliance Guardrails
- **Restricted Access Control:** Broadcast streams must terminate within an isolated private network enclave (VPC / On-Premise Stewards' Server) with role-based access control.
- **Cryptographic Lineage:** Every ingested video segment is hashed upon acquisition (SHA-256) and cataloged in an immutable manifest table.
- **Data Minimization:** Broadcast footage is retained only for the regulatory inquiry window (e.g., 96 hours post-event) unless sealed into an archived official inquiry case file.

---

## 3. High-Precision Annotation Schema & Protocol

To benchmark or fine-tune incident vision models under production conditions, ground truth annotations must adhere to the standardized MII schema.

### 3.1 Object Detection & Tracking (Vehicle Instances)
Annotations must be recorded per frame in normalized coordinates `[0.0, 1.0]`:
```json
{
  "frame_idx": 1420,
  "timestamp_utc": "2024-09-01T13:42:15.340000Z",
  "objects": [
    {
      "tracking_id": "CAR-VER-01",
      "driver_code": "VER",
      "car_number": 1,
      "team": "Red Bull Racing",
      "bbox_normalized": [0.3421, 0.4512, 0.5120, 0.6841],
      "occlusion_state": "PARTIAL_FRONT_WING",
      "wheel_positions": {
        "front_left": [0.3512, 0.6521],
        "front_right": [0.4910, 0.6480],
        "rear_left": [0.3601, 0.4620],
        "rear_right": [0.5050, 0.4590]
      }
    }
  ]
}
```

### 3.2 Track Limits & Track Geometry Annotations
- **Boundary Polylines:** White line edge coordinates and kerb edge boundaries annotated with sub-pixel precision.
- **Tire Contact Patch:** For track limit queries (Article 33.3 of the FIA Formula 1 Sporting Regulations), annotations must mark whether any part of all four tires remains in contact with the track boundary or beyond the white line.

### 3.3 Physical Contact & Incident Point Temporal Annotation
- **First Visual Contact ($t_{contact\_visual}$):** The exact frame index and timecode where physical bodywork or tire-to-tire contact is first observed.
- **Visual Separation ($t_{separation\_visual}$):** The frame where vehicle surfaces disengage.
- **Uncertainty Interval ($\pm \Delta t$):** Recorded based on camera frame interval (e.g., $\pm 10\text{ ms}$ for 50 fps, $\pm 2.5\text{ ms}$ for 200 fps).

---

## 4. Cross-Modal Telemetry Synchronization Protocol

A primary capability of MII is synthesizing optical evidence with high-frequency telemetry (FastF1 / OpenF1 / ECU CAN logs).

### 4.1 Temporal Alignment Methodology
```
Optical Timecode (SMPTE UTC)  <------------------------->  Telemetry Stream (GPS / Session UTC)
          |                                                             |
   Frame Timestamp                                               CAN Bus Timestamp
    (e.g., 50 Hz)                                                 (e.g., 100 Hz)
          \                                                             /
           \--- Cross-Correlation: Deceleration Peak vs Optical Impact --/
```

1. **Clock Harmonization:** Optical timecodes (SMPTE LTC) are aligned to session telemetry via GPS time references broadcast in the FIA timing feed.
2. **Dynamic Time Warping / Cross-Correlation:** Where absolute clock drift occurs ($< 200\text{ ms}$), alignment is anchored to known physical impulses:
   - Peak lateral/longitudinal jerk from onboard accelerometers ($a_x, a_y$).
   - Sharp wheel speed differential or steering angle correction.
   - Throttle release and sudden brake application.
3. **Discrepancy Reporting:** If optical contact and telemetry shock differ by $> 150\text{ ms}$, the system surfaces a `TEMPORAL_DISCREPANCY` triage alert for steward inspection.

---

## 5. Inter-Annotator Agreement (IAA) & Quality Control

To prevent cognitive bias or single-reviewer error during benchmark dataset authoring:
- **Dual-Blind Annotation:** Every incident sequence must be annotated independently by two certified sporting analysts or engineers.
- **Agreement Thresholds:**
  - **Bounding Box IoU:** $\text{IoU} \ge 0.88$ across non-occluded vehicle instances.
  - **Contact Frame Agreement:** Exact match within $\pm 1$ frame ($\pm 20\text{ ms}$ at 50 fps).
  - **Cohen’s Kappa ($\kappa$):** $\kappa \ge 0.85$ for categorical flags (e.g., track limit breach, contact occurrence).
- **Steward Resolution:** Cases failing agreement thresholds are escalated to a senior steward panel for arbitration, and the variance is archived in the dataset card.

---

## 6. Current Operational Realities & Path to Production

| Component | Current Repo State | Production Partner Requirements |
| :--- | :--- | :--- |
| **Broadcast Video Ingest** | `INSUFFICIENT_DATA` (Zero commercial video bundled) | FOM / Broadcaster API credentials & SRT stream access |
| **Telemetry Analysis** | Fully Operational (100% verified on FastF1 / Monza data) | Real-time live timing & telemetry bridge |
| **Regulation Retrieval** | Fully Operational (FIA Sporting Code & Regulations) | Annual regulatory document updates |
| **Steward Workspace** | Fully Operational (Full-stack UI, triage, & state machine) | Deployed on secure stewards' room touchscreens/monitors |
| **Adjudication Doctrine** | Strict Non-Adjudication Enforced | Preserved invariant: Human stewards make all decisions |

---

*This specification establishes the authoritative engineering standard for real-world visual data ingestion in Motorsport Incident Intelligence.*
