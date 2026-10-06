# Prompt 27 Pre-Implementation Uncertainty & Evidence Quality Audit

**Project:** Motorsport Incident Intelligence (MII)  
**Date:** October 2026  
**Status:** COMPLETE AUDIT  
**Scope:** Telemetry, Baseline, Geometry, Video/CV, ML Evidence, and Case Workspace  

---

## 1. Executive Summary & Audit Objectives

Motorsport adjudication operates in high-stakes environments where sensory streams are inherently noisy, discretely sampled, and subject to physical and temporal limitations. Treating derived numbers or model predictions as exact truth without explicit uncertainty envelopes introduces dangerous false precision and risks miscarriages of sporting justice.

This audit methodically reviews every measurement, derivation, and inference pipeline across MII to answer:
1. **What do we know?** (Direct sensor observations vs mathematical derivations vs statistical models)
2. **How do we know it?** (Sensor CAN-bus, GPS interpolation, 2D projection, bounding-box tracking, documentary archive)
3. **How reliable is the measurement?** (Explicit physical bounds: $\pm \Delta x$, $\pm \Delta v$, $\pm \Delta t$)
4. **Where does uncertainty propagate?** (Combined variance in differences: $\sigma_{\text{comb}} = \sqrt{\sigma_A^2 + \sigma_B^2}$)
5. **What evidence is missing?** (Unobserved broadcast video, missing telemetry channels, uncalibrated ML cohorts)
6. **What contradictions remain?** (Distinguishable divergences vs differences within measurement tolerance)
7. **What should a human steward investigate next?** (Deterministic `REVIEW_FOCUS` targets)

---

## 2. Multi-Layer Uncertainty & Error Budget Inventory

### 2.1. Telemetry Ingestion Layer (FastF1 / OpenF1)
- **Sensor Types:** ECU Wheel Speed Transducers, Brake Hydraulic Pressure Sensors, Fly-by-wire Throttle Pots, 10Hz/25Hz GPS / Timing Transponders.
- **Raw Sampling Cadence:** Asynchronous ECU broadcasts (typically 10Hz to 100Hz depending on channel).
- **Interpolation / Normalization:** Resampled onto a uniform 25Hz grid ($T_s = 0.040\text{ s}$).
- **Temporal Uncertainty ($\Delta t$):** $\pm 0.040\text{ s}$ (one resampling interval).
- **Cartesian Spatial Uncertainty ($\Delta x, \Delta y$):** $\pm 0.20\text{ m}$ (GPS and spline re-projection onto track reference line).
- **Wheel Speed Uncertainty ($\Delta v$):** $\pm 2.0\text{ km/h}$ ($\approx \pm 0.56\text{ m/s}$) from tire slip angle, rolling radius dynamic variation, and transducer quantization.
- **Brake / Throttle Percentage:** $\pm 1.0\%$ sensor noise; binary switch vs continuous hydraulic pressure calibration varies by team.
- **Derived Quantities & False Precision Risks:**
  - Minimum gap: $\text{gap} = \sqrt{(x_A - x_B)^2 + (y_A - y_B)^2}$. Combined spatial uncertainty is $\sqrt{0.20^2 + 0.20^2} \approx \pm 0.28\text{ m}$. Reporting `0.423817 m` is mathematically fraudulent; the value must be formatted as `0.42 m ± 0.28 m`.
  - Closing speed: Central finite difference $\Delta v_{\text{close}} = -\frac{\Delta d}{\Delta t}$. Highly sensitive to position noise at 25Hz; requires bounded derivative smoothing. Uncertainty $\approx \pm 1.5\text{ m/s}$ ($\pm 5.4\text{ km/h}$).

### 2.2. Reference Baseline Analysis Layer
- **Methodology:** Pointwise median comparison against clean, unimpeded laps (qualifying lap or teammate reference).
- **Sources of Variance:**
  - Track evolution / rubber accumulation ($\approx 0.1\text{ s}$ to $0.5\text{ s}$ per stint).
  - Tire degradation / compound differences ($\Delta \mu$ friction coefficient).
  - Fuel load mass difference (up to $100\text{ kg}$ over race distance $\rightarrow \approx 0.3\text{ s}$ per $10\text{ kg}$).
  - Ambient and track temperature drift ($\pm 5^\circ\text{C}$).
- **Spatial Braking Onset Tolerance:** Empirical baseline tolerance is $\pm 10.0\text{ m}$. Combined uncertainty of incident vs reference is $\sqrt{10.0^2 + 2.0^2} \approx \pm 10.2\text{ m}$. Any braking delta within $\pm 10.0\text{ m}$ is statistically indistinguishable from nominal race craft adjustments.

### 2.3. Overtake & Corner Geometry Layer
- **Vehicle Envelope:** Fixed 2D bounding boxes based on FIA regulatory dimensions ($5.63\text{ m} \times 2.00\text{ m}$).
- **Corner Apex Alignment:** Track distance parameterization ($s$-coordinate).
- **Uncertainty Sources:**
  - Car yaw / slip angle is not directly measured in standard 2D Cartesian GPS; orientation is inferred from velocity vector.
  - Front axle vs rear axle position calculation assumes zero crab/yaw deviation.
- **Apex Overlap Uncertainty:** Longitudinal axle separation tolerance $\pm 0.30\text{ m}$; overlap percentage tolerance $\pm 5.0\%$.

### 2.4. Video & Visual Computer Vision Layer
- **Broadcast Video Availability:** Commercially copyrighted by Formula One Management (FOM). When video files are unlinked, the status is strictly `UNAVAILABLE`.
- **Temporal Synchronization Envelope:** Broadcast camera frames (25fps or 50fps $\rightarrow \pm 0.040\text{ s}$ to $\pm 0.020\text{ s}$).
- **Spatial Computer Vision (2D YOLO / DeepSORT):**
  - Parallax and lens distortion: Fixed camera angles have non-linear focal perspectives and distance compression.
  - Bounding box jitter: Detection edge uncertainty $\pm 5$ to $15$ pixels.
  - Identity attribution: Car liveries, race numbers, helmet colors are prone to visual confusion during spins or smoke. Identity is strictly `MODEL_DERIVED` and must never be auto-adjudicated.

### 2.5. Machine Learning Interaction Pattern Layer
- **Model Role:** Telemetry interaction pattern detector ($y \in \{0, 1\}$ nominal vs anomalous multi-car interaction).
- **Cohort Size ($N_{sup} = 17$):** 5 incident candidates, 12 nominal controls across Monza and Red Bull Ring 2024.
- **Calibration Status:** Strictly marked `INSUFFICIENT_DATA`. With $N=17$, Platt scaling and isotonic calibration cannot yield statistically valid probability estimates ($\Delta Brier$ inconclusive).
- **Confidence vs Uncertainty:** The model output ($P(\text{anomaly}) = 0.88$) is a feature-space score, NOT a calibrated probability and NEVER a measure of driver fault. The uncertainty band is wide ($[0.72, 0.96]$).

---

## 3. Discrepancy & Combined Uncertainty Formulation

When cross-modal streams disagree, the system must determine whether the observed difference is mathematically distinguishable beyond combined measurement error:

$$\Delta_{\text{obs}} = |M_A - M_B|$$
$$\sigma_{\text{comb}} = \sqrt{\sigma_A^2 + \sigma_B^2}$$

### Evaluation Decision Table:
1. **Case 1: Indistinguishable**  
   $$\Delta_{\text{obs}} \le \sigma_{\text{comb}}$$  
   $$\text{Result: } \texttt{NOT\_CLEARLY\_DISTINGUISHABLE\_WITHIN\_UNCERTAINTY}$$  
   *Interpretation:* The discrepancy cannot be statistically separated from measurement noise. Stewards must be alerted that the streams are physically consistent within sensor precision limits.

2. **Case 2: Distinguishable**  
   $$\Delta_{\text{obs}} > \sigma_{\text{comb}}$$  
   $$\text{Result: } \texttt{DISTINGUISHABLE\_BEYOND\_UNCERTAINTY}$$  
   *Interpretation:* A genuine physical, temporal, or spatial divergence exists between evidence streams. This constitutes a high-priority inspection point for human stewards.

---

## 4. Deterministic Review Focus Engine (`REVIEW_FOCUS`)

The review focus generator synthesizes all gaps, high uncertainties, and distinguishable discrepancies into a prioritized checklist for the steward panel:

```
[STREAMS & MEASUREMENTS]
           │
           ├── Missing / Unavailable Streams  ──> Missing Evidence Actions
           ├── High Measurement Uncertainty   ──> Physical Verification Prompts
           ├── Distinguishable Discrepancies  ──> Divergence Investigation Tasks
           └── Small Sample Size ML Patterns  ──> Advisory Context Warnings
           │
           ▼
[DETERMINISTIC REVIEW FOCUS CHECKLIST]
  (Strictly non-adjudicative; zero penalties; zero fault attributions)
```

### Strict Non-Adjudicative Guardrails:
- **Never:** "Investigate Driver A for causing a collision."
- **Never:** "Driver B is at fault."
- **Never:** "Impose a 5-second penalty."
- **Always:** "Inspect telemetry channel X at T=13:42:18.4 due to measurement uncertainty ±0.20m."
- **Always:** "Cross-reference broadcast camera 3 to verify identity attribution given unlinked video stream."

---

## 5. Implementation Roadmap

1. **Contracts & Schemas (`contracts.py`, `workspace.py`):**
   - Formalize `EvidenceQualityLevel`, `EvidenceAvailabilityLevel`, `UncertaintySpecification`, `ReviewFocus`.
   - Update `WorkspaceEvidenceItem` and `StewardCaseWorkspace` with formatted uncertainties and `review_focus`.
2. **Numerical Precision Formatter (`backend/app/evidence/formatting.py`):**
   - Implement `format_with_uncertainty(value, uncertainty, unit)`.
3. **Discrepancy Uncertainty Evaluator (`consistency.py`):**
   - Calculate $\sigma_{\text{comb}}$ and tag discrepancies with distinguishable status.
4. **Timeline Uncertainty Envelopes (`workspace_service.py`):**
   - Attach explicit timestamp and spatial uncertainties to every milestone.
5. **Deterministic Review Focus Generator (`workspace_service.py`):**
   - Deterministically generate non-adjudicative investigation checklist.
6. **Frontend Panels:**
   - Display Review Focus banner and uncertainty badges.
7. **Testing & Validation:**
   - Implement comprehensive 16+ test suite in `test_evidence_quality.py`.
