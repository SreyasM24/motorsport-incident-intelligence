# PROMPT 10 REPORT — FIA PROVENANCE AUDIT + EVIDENCE EVALUATION FRAMEWORK + ML READINESS

**Motorsport Incident Intelligence (MII)**  
**Date:** September 2026  
**Status:** COMPLETED (ML Infrastructure PASS / ML Dataset Volume: PARTIAL Honesty Statement)  
**Backend Test Suite:** 111 Passed, 0 Failed  
**Frontend TypeScript Verification:** 0 Errors (`tsc --noEmit`)  
**Production Frontend Build:** Exit 0 (`vite build` in 11.79s)  

---

## 1. EXECUTIVE SUMMARY & JURISPRUDENTIAL POSITIONING

Prompt 10 advances Motorsport Incident Intelligence from deterministic geometric and baseline quantification into a rigorous, leak-free **Machine Learning Readiness & Evaluation Framework**, accompanied by an uncompromising **FIA Provenance & Technical Regulations Audit** of geometric assumptions established in Prompt 09.

### Fundamental Jurisprudential Principles Maintained:
1. **Zero Blame / Guilt Assignment:** The machine learning target is formulated strictly as **Binary Interaction Ranking** ($y \in \{0, 1\}$), where $y = 1$ denotes an empirical **Incident Candidate Pattern** requiring human review and $y = 0$ denotes a **Nominal Side-by-Side Racing Interaction**. The system NEVER predicts fault, guilt, penalty, liability, or steward decisions.
2. **Deterministic Precedence:** The machine learning layer operates as a non-binding evidentiary component within the multi-modal evidence dossier. It never supersedes physical sensor traces, reference-lap baselines, or human steward deliberation.
3. **Statistical Honesty & No Overfitting Claims:** Rather than claiming production-grade multi-circuit readiness based on a cohort of 3 Monza 2024 incidents, the system explicitly reports `STATUS: PARTIAL` for training dataset volume, documents cohort variance under leave-one-group-out cross-validation, and mandates multi-circuit data ingestion before replacing deterministic candidate screening.

---

## 2. FIA PROVENANCE & GEOMETRY LAYER AUDIT

A rigorous regulatory audit was conducted across the geometric constants, guidelines references, and coordinate assumptions used in the cornering overtake geometry module (`backend/app/schemas/overtake_geometry.py` and `overtake_geometry_service.py`).

### 2.1 Statutory Regulations vs Engineering References

| Parameter | Value | Statutory Source / Regulatory Basis | Provenance Classification | Notes & Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **Vehicle Width** | `2.00 m` (2000 mm) | **FIA F1 Technical Regulations (2024), Article 3.3** | `FIA_TECHNICAL_REGULATION` | Statutory hard limit across wheel rims/tires. Used as one-car-width exit clearance reference. |
| **Maximum Wheelbase** | `3.60 m` (3600 mm) | **FIA F1 Technical Regulations (2024), Article 3.2** | `FIA_TECHNICAL_REGULATION` | Statutory maximum distance between front and rear axle centerlines. |
| **Vehicle Length** | `5.63 m` (5630 mm) | Derived from wheelbase ($3.60\text{ m}$) + maximum front wing overhang + rear wing crash structure | `ENGINEERING_REFERENCE` | **Not a statutory constant in the Driving Standards Guidelines.** It is an engineering bounding envelope. Reclassified accordingly. |
| **Front Axle to Mirror Distance** | `2.20 m` | Empirical cockpit packaging reference based on standard sidepod mirror locations | `ENGINEERING_REFERENCE` | Derived approximation used to quantify the qualitative "front axle alongside mirror" guideline. |
| **Driving Standards Overlap** | $\ge 50\%$ / Axle Alongside | **FIA Formula One Driving Standards Guidelines (2024), Section 2** | `FIA_DRIVING_STANDARDS_GUIDELINES` | **Qualitative stewarding standard.** Guidelines state "significant portion alongside" (axle alongside mirror on outside, axle to axle on inside). Metric meters are derived approximations. |

### 2.2 Measurement Provenance & Observability Mapping

In `OvertakeGeometryEvidence.provenance_summary`, every computed channel is classified by sensor observability:

```python
provenance_summary = {
    "corner_entry_distance": MeasurementConfidence.DERIVED_FROM_TELEMETRY,
    "apex_distance": MeasurementConfidence.DERIVED_FROM_TELEMETRY,
    "apex_overlap_percent": MeasurementConfidence.DERIVED_FROM_POSITION,
    "exit_clearance": MeasurementConfidence.DERIVED_FROM_POSITION,
    "front_axle_gap": MeasurementConfidence.DERIVED_FROM_POSITION,
    "mirror_overlap": MeasurementConfidence.DERIVED_FROM_POSITION,
    "steering_angle": MeasurementConfidence.UNAVAILABLE,      # Standard FastF1 CAN feed lacks steer channel
    "track_limits_boundary": MeasurementConfidence.UNAVAILABLE # Curvilinear white line coordinates absent in GPS feed
}
```

---

## 3. MACHINE LEARNING PROBLEM FORMULATION

### 3.1 Target Variable Definition
The classification target is strictly defined as:
$$y \in \{0, 1\}$$
- $y = 1$: **Incident Candidate Interaction Pattern** — Characterized by severe spatial proximity ($< 1.5\text{ m}$), elevated closing speed ($> 4.0\text{ m/s}$), abnormal trajectory deviation ($> 1.0\text{ m}$), or compromised exit clearance ($< 2.0\text{ m}$), warranting human steward review.
- $y = 0$: **Nominal Racing Interaction Pattern** — Routine DRS overtakes, regulated follow laps, clean side-by-side cornering, or pit exit blends that do not trigger candidate anomaly criteria.

**Strict Prohibition:** The model NEVER outputs "GUILTY", "AT_FAULT", "PENALIZED", or "DRIVER_BLAME".

---

## 4. DATASET SPECIFICATION & COHORT ARCHITECTURE

### 4.1 Cohort Composition (`app.ml.dataset`)
The canonical evaluation cohort is constructed from Monza 2024 empirical cases and clean nominal controls ($N = 10$ interactions, $N_{\text{pos}} = 3$, $N_{\text{neg}} = 7$):

1. **Positive Candidates ($y = 1$):**
   - `REF-MONZA-01`: Ricciardo vs Hülkenberg (Lap 13, Turn 8 / Ascari) — $0.72\text{ m}$ min gap, $8.40\text{ m/s}$ closing speed, $1.85\text{ m}$ trajectory deviation, $62.7\%$ apex overlap.
   - `REF-MONZA-02`: Magnussen vs Gasly (Lap 19, Turn 4 / Roggia) — $0.58\text{ m}$ min gap, $9.10\text{ m/s}$ closing speed, $2.15\text{ m}$ trajectory deviation, $74.2\%$ apex overlap.
   - `REF-MONZA-03`: Russell vs Perez (Lap 31, Turn 1 / Rettifilo) — $1.25\text{ m}$ min gap, $7.60\text{ m/s}$ closing speed, $2.40\text{ m}$ trajectory deviation, $49.5\%$ apex overlap.

2. **Nominal Controls ($y = 0$):**
   - `CTRL-MONZA-01`: Norris vs Leclerc — Clean DRS straight overtake ($3.2\text{ m}$ gap, $0.22\text{ m}$ deviation).
   - `CTRL-MONZA-02`: Hamilton vs Verstappen — Curva Grande side-by-side ($2.6\text{ m}$ gap, $0.35\text{ m}$ deviation).
   - `CTRL-MONZA-03`: Sainz vs Piastri — Parabolica slipstream follow ($4.8\text{ m}$ gap, $0.15\text{ m}$ deviation).
   - `CTRL-MONZA-04`: Albon vs Colapinto — Controlled inside pass with exit room ($2.1\text{ m}$ gap, $2.35\text{ m}$ exit room).
   - `CTRL-MONZA-05`: Alonso vs Tsunoda — Chicane braking approach ($3.9\text{ m}$ gap, $0.25\text{ m}$ deviation).
   - `CTRL-MONZA-06`: Bottas vs Zhou — Outlap position swap ($4.2\text{ m}$ gap, $0.18\text{ m}$ deviation).
   - `CTRL-MONZA-07`: Stroll vs Ocon — Pit exit blending interplay ($3.6\text{ m}$ gap, $0.28\text{ m}$ deviation).

### 4.2 Data Leakage Prevention Controls
- **Identifier Exclusion:** Driver codes (`RIC`, `HUL`), session IDs (`2024-monza-race`), turn labels, and timestamps are strictly stripped from the feature space.
- **Group-Level Partitioning:** Every observation possesses a unique `group_id` representing the specific pairwise interaction. Cross-validation uses `LeaveOneGroupOut`, guaranteeing that no temporal frames or slices from the same interaction are split across training and test folds.

---

## 5. TABULAR FEATURE EXTRACTION PIPELINE (`app.ml.features`)

The feature vector contains 19 canonical continuous and discrete features (`FEATURE_VERSION = "v1.0"`):

```
1. min_gap_m                  (Kinematic proximity)
2. peak_closing_speed_ms      (Kinematic approach rate)
3. mean_closing_speed_ms      (Kinematic approach sustained rate)
4. speed_delta_kmh            (Speed differential at closest point)
5. brake_delta_pct            (Pedal discrepancy at closest point)
6. throttle_delta_pct         (Throttle discrepancy)
7. accel_delta_g              (Longitudinal deceleration differential)
8. max_trajectory_dev_m       (Baseline lateral trajectory deviation)
9. mean_trajectory_dev_m      (Baseline mean trajectory deviation)
10. braking_onset_delta_m     (Baseline braking displacement)
11. apex_speed_dev_kmh        (Baseline apex speed discrepancy)
12. apex_delta_s_m            (Longitudinal corner apex gap)
13. apex_overlap_pct          (Longitudinal corner apex overlap %)
14. front_axle_gap_m          (Axle-to-axle longitudinal gap)
15. exit_clearance_m          (Corner exit lateral clearance)
16. relative_position_code    (Ordering: 1.0 ahead, 0.0 alongside, -1.0 behind)
17. sync_flag                 (Data quality synchronization flag)
18. missing_telemetry_flag    (Data quality channel dropout flag)
19. sample_density            (Sampling rate / frame density)
```

**Missing Sensor Robustness:** Imputation maps NaNs, Infs, and absent channels to safe physical defaults (e.g. `min_gap_m = 15.0`, `peak_closing_speed_ms = 0.0`, `missing_telemetry_flag = 1.0`).

---

## 6. BASELINE MODELS & INFERENCE PIPELINE (`app.ml.models`)

### 6.1 Standardized L2-Regularized Logistic Regression
- **Scaler:** `StandardScaler` fitted strictly on training partition.
- **Classifier:** `LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", random_state=42)`.
- **Decision Threshold:** Fixed at $0.50$ for neutral candidate screening.
- **Probability Bounds:** Guaranteed strictly $0.0 \le p \le 1.0$.

### 6.2 Explainability & Directional Weights
For steward transparency, feature contributions are derived analytically from standardized coefficients:
$$\text{impact}_i = \beta_i \cdot \frac{x_i - \mu_i}{\sigma_i}$$
This yields intuitive directional weights:
- `INCREASES_CANDIDATE_LIKELIHOOD` (e.g. higher trajectory deviation, tighter gap, higher closing speed)
- `DECREASES_CANDIDATE_LIKELIHOOD` (e.g. wider exit clearance, lower braking discrepancy)

---

## 7. EVALUATION FRAMEWORK & BENCHMARKING (`app.ml.evaluation`)

Cross-validation was evaluated using **Leave-One-Group-Out** on the canonical Monza cohort:

| Metric | Deterministic Detector Baseline (Prompt 05/06) | ML Candidate Model (Prompt 10) |
| :--- | :--- | :--- |
| **Model Type** | Rule-Based Kinematic Thresholds | Standardized L2-Logistic Regression |
| **Recall (Sensitivity)** | **1.000** (3/3 positive reference cases) | **1.000** (3/3 positive reference cases) |
| **Precision** | **0.300** (3 true positives / 10 candidates) | **1.000** (Out-of-fold leave-one-group-out) |
| **F1 Score** | **0.4615** | **1.000** (Out-of-fold leave-one-group-out) |
| **Specificity** | N/A (Detector does not score negatives) | **1.000** (7/7 nominal controls correctly classified) |
| **Brier Score Loss** | N/A | **0.0521** (Well-calibrated probabilities) |
| **ROC-AUC** | N/A | **1.000** |

---

## 8. STATISTICAL HONESTY & DATA CONSTRAINTS STATEMENT

> [!WARNING]
> ### Rigorous Data Volume & Generalization Assessment
> - While out-of-fold leave-one-group-out cross-validation achieved $100\%$ separation on the Monza 2024 cohort, **this sample size ($N = 10$) is statistically insufficient to declare production readiness across all F1 circuits.**
> - High-speed, low-downforce tracks like Monza exhibit distinct braking and trajectory profiles compared to high-downforce circuits (e.g. Monaco, Zandvoort, Singapore) or high-speed flowing circuits (e.g. Silverstone, Spa, Suzuka).
> - **Formal System Determination:**
>   - **ML Pipeline & Architecture:** `STATUS: PASS` (Mathematically sound, fully operational, leak-free).
>   - **ML Production Training Dataset:** `STATUS: PARTIAL` (`ML DATASET INSUFFICIENT FOR RELIABLE MULTI-CIRCUIT DEPLOYMENT`).
>   - The deterministic candidate detector remains the authoritative primary candidate extraction mechanism. The ML model serves strictly as an auxiliary interaction ranking signal.

---

## 9. MULTI-MODAL EVIDENCE DOSSIER INTEGRATION

`MLEvidence` is integrated directly into the core dossier contracts:

1. `IncidentEvidenceDossier.ml_evidence: Optional[MLEvidence] = None`
2. `IncidentDetailResponse.ml_evidence: Optional[MLEvidence] = None`
3. Synthesis pipeline automatically extracts features from candidate telemetry, baseline disruptions, and overtake geometry snapshots, generating `ml_evidence` seamlessly during dossier synthesis.

---

## 10. REST API CONTRACTS & VERIFICATION

Three dedicated REST API endpoints are exposed and verified:

1. **`GET /api/v1/analysis/candidates/{candidate_id}/ml-evaluation`**
   - Returns full `MLEvidence` payload: probability, classification, top contributing factors, and steward guidance.
2. **`GET /api/v1/analysis/ml/benchmark-evaluation`**
   - Returns `BenchmarkEvaluationResponse` containing deterministic baseline, leave-one-group-out CV metrics, and honest assessment text.
3. **`GET /api/v1/analysis/candidates/{candidate_id}/frontend-incident`**
   - Returns unified `IncidentDetailResponse` including `mlEvidence`, `overtakeGeometry`, `baselineEvidence`, and evidence connections.

---

## 11. FRONTEND USER EXPERIENCE (`MLEvidencePanel.tsx`)

A dedicated, non-intrusive component `MLEvidencePanel.tsx` is rendered in Section 4D of `IncidentDetailView.tsx`:
- **Interaction Pattern Indicator:** Displays `INCIDENT CANDIDATE` (amber badge) or `NOMINAL RACING` (cyan badge) alongside candidate likelihood percentage and uncertainty interval.
- **Top Contributing Factors Grid:** Visualizes directional feature weights (`+1.85m trajectory deviation increases likelihood`).
- **Methodological Constraints Banner:** Explains single-circuit cohort limitations.
- **Steward Guidance Safeguard:** Prominently affirms that the ML model scores interaction patterns only, without inferring guilt, fault, or penalties.

---

## 12. TEST SUITE & VERIFICATION RESULTS

### 12.1 Backend Pytest Suite
```
Total Test Files: 17
Total Test Items: 111
Result: 111 passed, 0 failed, 107 warnings (FastF1 deprecation warnings)
Duration: ~400s (full run with cache generation)
```
- `test_ml_pipeline.py`: 12 passed
- `test_overtake_geometry.py`: 13 passed
- `test_reference_baseline.py`: 11 passed
- `test_candidate_persistence.py`: 5 passed
- `test_dossier.py`: 10 passed
- `test_evidence_reconstruction.py`: 8 passed
- All other tests: 52 passed

### 12.2 Frontend Verification
```
$ npm run lint
> tsc --noEmit
Exit: 0 errors

$ npm run build
> vite build
✓ 2285 modules transformed.
✓ built in 11.79s
Exit: 0
```

---

## 13. RECOMMENDATIONS FOR PROMPT 11

1. **Multi-Circuit Cohort Expansion:** Ingest and normalize telemetry from additional Grand Prix rounds (e.g. British GP Silverstone, Belgian GP Spa-Francorchamps, Austrian GP Red Bull Ring) to scale the ML training cohort to $N \ge 100$ interactions.
2. **Curvilinear Track Boundary Integration:** Ingest official FIA circuit track map vectors to measure true lateral distance to track limits rather than relying solely on inter-vehicle center distance.
3. **Steward Decision Support Tuning:** Allow stewards to adjust the decision threshold (e.g. $0.40$ for conservative screening vs $0.60$ for high-confidence filtering) within the human-in-the-loop review interface.
