# System Boundaries and Epistemic Limitations

The Motorsport Incident Intelligence (MII) system is deliberately designed with strict operational, physical, and epistemic boundaries. This document articulates these boundaries to ensure correct interpretation by engineering teams, race directors, and officiating stewards.

---

## 1. Epistemic Guardrails: What the System Does NOT Do

### 1. No Autonomous Rulings
MII does not make verdicts, rule on racing incidents, or determine driver liability. The platform provides structured, verified evidence to assist human stewards in their deliberative duties.

### 2. No Fault or Guilt Classifiers
The system contains zero classification algorithms trained to output "Guilty", "At Fault", "Wholly Responsible", or "Predominantly Responsible". Assigning culpability requires legal and sporting judgment that cannot be delegated to an automated algorithm.

### 3. No Penalty Recommendations
The platform does not suggest time penalties, grid drop sanctions, penalty points, or reprimands. Sanctions are governed by judicial discretion and contextual championship factors outside machine telemetry.

### 4. No Intent Determination
Telemetry reveals *what* the car did (throttle trace, steering angle, trajectory path). It cannot reveal *why* the driver acted or what the driver intended. MII presents objective behavioral deltas without inferring driver malice, negligence, or premeditation.

---

## 2. Sensor & Physical Measurement Limitations

### GPS Sample Rate & Multipath Noise
- Official GPS telemetry is broadcast at approximately 4Hz to 10Hz. While spline interpolation creates a continuous 25Hz path, micro-movements within a $100\text{ms}$ interval remain subject to interpolation uncertainty.
- In venues with high grandstands, tree cover, or atmospheric interference, raw GPS position has a typical variance of $\pm 0.2\text{m}$.
- **System Mitigation**: Position measurements are cross-referenced with wheel speed sensors and onboard inertial measurement units (IMU) to bound positional error.

### CAN Bus Telemetry Resolution
- Steering angle, brake pressure, and throttle position are quantized by onboard Electronic Control Units (ECUs). Small driver inputs (e.g. steering corrections $< 1.5^\circ$) may fall within sensor deadbands.

---

## 3. Optical & Computer Vision Limitations

### Perspective Distortion & Parallax
- 2D broadcast camera lenses introduce radial and tangential distortion, along with intense optical compression when filming down long straights.
- Two cars that appear to touch visually may have substantial lateral separation in real space.
- **System Mitigation**: The system never uses visual bounding box overlap alone to establish contact; it requires corroboration from IMU accelerometer spikes.

### Visual Occlusion & Motion Blur
- High-speed cornering produces motion blur that can degrade bounding box localization precision.
- Wheel-to-wheel battles often result in partial or total occlusion of the inside vehicle.
- **System Mitigation**: The ByteTrack tracker utilizes Kalman filter state estimation during occluded frames, reporting lowered detection confidence until visibility is restored.

---

## 4. Operational Boundaries

- **Network Dependency**: Live streaming features require reliable network connectivity to ingest OpenF1 feeds. In the event of network disruption, the system falls back to cached local storage.
- **Circuit Baseline Availability**: Delta metrics (such as $\Delta \text{Brake}$) require at least 3 clean reference laps on comparable tire compounds and fuel loads. In changing weather conditions (e.g., intermediate wet to dry), reference lap validity degrades and is explicitly flagged as such.
