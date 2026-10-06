# Motorsport Incident Intelligence — Evidence Quality, Uncertainty Propagation & Epistemic Typing

This document formalizes the evidence quality architecture, physical measurement uncertainty propagation, epistemic typing taxonomy, and non-adjudicative steward inspection guidance within the Motorsport Incident Intelligence (MII) system.

---

## 1. Core Architectural Doctrines

### 1.1 Non-Adjudicative Mandate
The AI and algorithmic layers exist strictly to extract, synchronize, evaluate measurement tolerances of, and present empirical evidence to human stewards.
- The system **never** predicts guilt, fault, liability, violation, or penalty recommendations.
- All evidence outputs serve as empirical support for the human panel of FIA/series stewards.

### 1.2 Separation of Epistemic Dimensions
Three fundamentally different concepts are strictly separated and never conflated:
1. **Measurement Uncertainty ($\sigma$):** Physical sensor, sampling, and discretization tolerances of instrumented hardware (GPS, CAN wheel speed sensors, ECU clocks, optical broadcast cameras).
2. **Model Confidence ($P(\hat{y}|x)$):** Mathematical conditional probabilities emitted by supervised machine learning models conditioned on specific feature vectors.
3. **Evidence Availability:** Whether a data stream is present, partially synchronized, degraded, or unavailable (e.g. unlinked commercial broadcast footage).

### 1.3 Doctrine of Multidimensional Quality (No Single Aggregate Score)
Safety-critical motorsport adjudication cannot reduce disparate evidence streams (GPS coordinate bounds, CAN bus braking pressure, 2D broadcast parallax, documentary regulations) into a single scalar "reliability score" (e.g. *87% reliable*).
- Aggregation hides critical failure modes behind high numbers in other dimensions.
- The system enforces `MULTIDIMENSIONAL_NO_AGGREGATE_SCORE` as an architectural guarantee. Every evidence subsystem reports its own availability, precision, sensor bounds, and epistemic classification independently.

---

## 2. Sensor Precision & Uncertainty Envelopes

| Modality / Sensor | Raw Resolution | Physical Uncertainty ($\sigma$) | Epistemic Classification |
| :--- | :--- | :--- | :--- |
| **GPS Position (X, Y)** | Sub-centimeter raw float | $\pm 0.20\text{ m}$ per coordinate axis | `OBSERVED` |
| **Derived Euclidean Gap** | $d = \sqrt{\Delta x^2 + \Delta y^2}$ | $\pm 0.28\text{ m}$ ($\sqrt{4 \times 0.20^2}$) | `DERIVED` |
| **CAN Bus Wheel Speed** | 0.1 km/h | $\pm 2.0\text{ km/h}$ dynamic tire slip / slip angle | `OBSERVED` |
| **CAN Throttle / Brake** | 8-bit / 10-bit integer | $\pm 1\%$ travel / $\pm 2\text{ bar}$ line pressure | `OBSERVED` |
| **Timecode / Timestamp** | 25 Hz / 40 ms sampling | $\pm 0.040\text{ s}$ ($\pm 1$ sampling epoch) | `OBSERVED` |
| **Baseline Braking Delta**| Spatial difference | $\pm 10.2\text{ m}$ ($\sqrt{2.0^2 + 10.0^2}$) | `DERIVED` |
| **ML Interaction Pattern**| Probability output | Cohort $N=17$; Calibration `INSUFFICIENT_DATA` | `MODEL_DERIVED` |
| **Broadcast Video Stream**| 25 fps broadcast | `UNAVAILABLE` (commercial broadcast unlinked) | `UNAVAILABLE` |

### 2.1 Scientific Numerical Formatting & Precision Rules
To prevent false precision that could mislead human reviewers:
- **Spatial Distances:** Formatted to 2 decimal places with uncertainty envelope (e.g., `0.42m [±0.28m]`).
- **Velocities:** Formatted to 1 decimal place with uncertainty envelope (e.g., `284.5 km/h [±2.0 km/h]`).
- **Time Offsets:** Formatted to 3 decimal places with epoch bounds (e.g., `+0.120s [±0.040s]`).

---

## 3. Cross-Modal Discrepancy & Statistical Distinguishability

When comparing two independent evidence streams $A$ and $B$ (e.g., telemetry braking onset vs clean baseline lap, or optical tracking apex gap vs telemetry Euclidean distance), the system computes combined standard uncertainty:

$$\sigma_{\text{comb}} = \sqrt{\sigma_A^2 + \sigma_B^2}$$

### Distinguishability Criterion
A discrepancy with magnitude $|\Delta|$ is classified as:
- **`DISTINGUISHABLE_BEYOND_UNCERTAINTY`** if:
  $$|\Delta| > \sigma_{\text{comb}}$$
  *Meaning:* The observed difference exceeds physical sensor and baseline noise bounds and represents an empirical anomaly warranting steward inspection.
- **`WITHIN_UNCERTAINTY_MARGIN`** if:
  $$|\Delta| \le \sigma_{\text{comb}}$$
  *Meaning:* The observed difference is fully explainable by sensor noise, discretization, or lap-to-lap baseline variance; human stewards should treat the streams as physically consistent.

---

## 4. Prioritized Steward Review Focus Engine

Rather than emitting automated verdicts, the system generates an empirical checklist of prioritized inspection targets (`review_focus`) tailored to the specific case:
1. **Physical Contact Uncertainty Bounds:** If lateral gap is $< 1.0\text{ m}$, warns that peak approach is within sensor tolerances ($\pm 0.28\text{ m}$) and directs stewards to onboard cameras and vehicle bodywork scuffs.
2. **Missing Video Warning:** If commercial broadcast video is unlinked (`UNAVAILABLE`), directs stewards to FIA CCTV and race control timing monitors without bias.
3. **Statistically Distinguishable Discrepancies:** Highlights discrepancies whose magnitude exceeds $\sigma_{\text{comb}}$ (e.g., braking onset differing by $>10.2\text{ m}$ from reference laps).
4. **Model-Derived Limitations:** Explicitly flags supervised ML prototype cohort size ($N=17$) and uncalibrated status (`INSUFFICIENT_DATA`), reminding stewards that ML predictions are purely kinematic pattern detection.

---

## 5. API Endpoints

- `GET /api/v1/cases/{candidate_id}/workspace`: Complete steward workspace including review focus, timeline with uncertainty envelopes, triage items, and quality matrix.
- `GET /api/v1/cases/{candidate_id}/review-focus`: Dedicated endpoint returning prioritized non-adjudicative inspection targets.
- `GET /api/v1/cases/{candidate_id}/evidence-quality`: Dedicated endpoint returning the multidimensional quality matrix with explicit `MULTIDIMENSIONAL_NO_AGGREGATE_SCORE` doctrine.
