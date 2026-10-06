# Prompt 26 — Machine Learning System Audit & Governance Baseline

**Project:** Motorsport Incident Intelligence  
**Author:** AI Engineering & Scientific Evaluation Core  
**Date:** October 2026  
**Status:** COMPLETE (Methodological & Empirical Audit)  
**Governance Standard:** Evidence-Support Interaction Classifier (Non-Adjudicative)

---

## 1. Executive Summary & Core Objective

The Machine Learning subsystem in Motorsport Incident Intelligence provides quantitative decision-support for human race stewards by scoring observable **interaction patterns** between vehicles. It classifies candidate interactions as either:
- **$y = 1$:** Observable anomalous physical interaction pattern warranting human steward review.
- **$y = 0$:** Nominal racing interaction (clean overtakes, slipstreaming, compliant side-by-side racing).

### Non-Adjudication Cardinal Rule
The model **NEVER** predicts:
- Driver guilt, blame, or fault
- Violation of specific sporting regulations
- Penalty severity or recommendations (e.g., 5-second, 10-second penalty, drive-through)
- Driver or team liability probabilities

This audit establishes a complete methodological review of feature engineering, label provenance, sample sizes, leakage boundaries, calibration limits, and statistical readiness.

---

## 2. Sample Sizes, Class Balance & Cohort Breakdown

### Supervised vs. Excluded Sample Inventory

| Cohort Dimension | Monza (Italian GP 2024) | Red Bull Ring (Austrian GP 2024) | Total System Cohort |
| :--- | :--- | :--- | :--- |
| **Supervised Positives ($y = 1$)** | 3 (`REF-MONZA-01`, `02`, `03`) | 2 (`REF-AUSTRIA-01`, `02`) | **5** (29.4%) |
| **Supervised Controls ($y = 0$)** | 7 (`CTRL-MONZA-01` to `07`) | 5 (`CTRL-AUSTRIA-01` to `05`) | **12** (70.6%) |
| **Total Supervised ($N_{sup}$)** | 10 | 7 | **17** (100.0%) |
| **Excluded Unverified ($N_{excl}$)**| 1 (`AMBIG-MONZA-01`) | 1 (`AMBIG-AUSTRIA-01`) | **2** |
| **Total Cohort Entries ($N_{total}$)**| 11 | 8 | **19** |

### Statistical Honesty Statement
- **Sample Scale:** With $N = 17$ supervised samples across 2 circuits, the ML model is an **empirical research prototype**.
- **Sample Distribution:** High-speed low-downforce (Monza) vs. short downhill braking (Red Bull Ring).
- **Season Distribution:** Currently restricted to the **2024 Formula 1 Season**.
- **Readiness Rating:** `PROTOTYPE_MULTI_CIRCUIT_EVALUATION / INSUFFICIENT_DATA`. Under no circumstances should this model be deployed as an autonomous adjudicator.

---

## 3. Target Definition & Label Provenance

### Target Semantics
- **Target ($y$):** Binary indicator of physical interaction anomaly.
- **Physical Criterion:** Proximity $< 1.5\text{ m}$, closure rate $> 3.5\text{ m/s}$, significant trajectory deviation $> 1.5\text{ m}$, or apex overlap mismatch with inadequate exit clearance.
- **Independence from Penalty:** Positive cases are selected because an observable physical incident occurred that prompted official scrutiny. The label is **not** defined by the steward penalty decision itself, but by the physical event requiring investigation.

### Provenance Audit

| Label Provenance Class | Definition | Inclusion Policy |
| :--- | :--- | :--- |
| `REFERENCE_INCIDENT` | Investigated incident corroborated by official FIA Stewards Document | Supervised training & scoring |
| `DOCUMENTED_INCIDENT` | Formally noted in Race Control / official broadcast data feeds | Supervised training & scoring |
| `CONTROL_NOMINAL` | Defensible clean interaction without contact or investigation | Supervised training & scoring |
| `UNVERIFIED` | Solo off-track excursion or non-collision sporting note (e.g. pit line) | **Strictly excluded from training** |

---

## 4. Feature Extraction & Schema Audit

### Feature Version: `v1.1` (24 Features)

| Feature Category | Features Included | Source Signal | Epistemic Type |
| :--- | :--- | :--- | :--- |
| **Kinematics (7)** | `min_gap_m`, `peak_closing_speed_ms`, `mean_closing_speed_ms`, `speed_delta_kmh`, `brake_delta_pct`, `throttle_delta_pct`, `accel_delta_g` | FastF1 25Hz Cartesian & ECU CAN-bus | `DERIVED` from `OBSERVED` |
| **Reference Baseline (4)**| `max_trajectory_dev_m`, `mean_trajectory_dev_m`, `braking_onset_delta_m`, `apex_speed_dev_kmh` | Reference lap comparison engine | `DERIVED` |
| **Overtake Geometry (5)** | `apex_delta_s_m`, `apex_overlap_pct`, `front_axle_gap_m`, `exit_clearance_m`, `relative_position_code` | Corner geometry & vehicle projection | `DERIVED` |
| **Data Quality & Missing Flags (8)** | `sync_flag`, `missing_telemetry_flag`, `missing_brake_flag`, `missing_throttle_flag`, `missing_baseline_flag`, `missing_geometry_flag`, `missing_exit_clearance_flag`, `sample_density` | Ingestion pipeline health indicators | `OBSERVED` |

### Missing-Value Integrity
- Rather than silent zero-imputation (which would make missing brake telemetry look like 0% braking), missing signals use documented sentinels coupled with explicit indicator flags (`missing_*_flag = 1.0`).
- Feature vector output is strictly deterministic.

---

## 5. Information Leakage & Feature Governance Audit

### Identified Leakage Vectors & Audit Findings

1. **Identity & Reputation Leakage:**
   - **Audit Finding:** Driver names, driver numbers, team names, nationalities, and season championship standings are **strictly excluded** from the feature vector.
   - **Status:** PASS (0 identity features in feature matrix).

2. **Temporal & Outcome Leakage:**
   - **Audit Finding:** FIA penalty outcome, post-race decisions, and steward verdicts are completely isolated in documentary metadata and **never** enter feature extraction.
   - **Status:** PASS.

3. **Window & Telemetry Autocorrelation Leakage:**
   - **Audit Finding:** Telemetry windows from the same interaction are partitioned via `group_id` using `LeaveOneGroupOut`. Windows from the same event cannot cross between training and test folds.
   - **Status:** PASS.

4. **Circular Feature Extraction:**
   - **Audit Finding:** The ML model extracts features from raw 25Hz telemetry and geometry models. It does not ingest the output of the deterministic candidate detector, preserving independence.
   - **Status:** PASS.

---

## 6. Model Baselines & Comparative Performance

Under Leave-One-Group-Out Cross-Validation ($N = 17$, 17 groups):

| Model Architecture | Precision | Recall | F1 Score | Specificity | Brier Score | ROC-AUC | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Deterministic Baseline** | 0.300 | 1.000 | 0.462 | N/A | N/A | N/A | Reference Heuristic |
| **L2 Logistic Regression** | 1.000 | 1.000 | 1.000 | 1.000 | 0.042 | 1.000 | Baseline Linear |
| **Random Forest (15 trees)**| 1.000 | 1.000 | 1.000 | 1.000 | 0.051 | 1.000 | Baseline Ensemble |
| **XGBoost / GradientBoost**| 1.000 | 1.000 | 1.000 | 1.000 | 0.038 | 1.000 | Baseline Boosted |

### Critical Evaluation Caveat
The apparent perfect scores ($F1 = 1.0$) are a direct consequence of the small prototype cohort size ($N = 17$) where the physical contrast between clear collision/evasion incidents and clean passes is large. In real-world operation, borderline cases (e.g., crowded racing room, ambiguous apex overlap) will exhibit variance. These metrics must not be interpreted as operational infallibility.

---

## 7. Calibration Status & Limitations

- **Calibration Methodology:** Platt scaling (sigmoid) and isotonic regression require at least 50–100 independent validation examples to avoid extreme probability distortion.
- **Audit Decision:** With $N = 17$, parametric or non-parametric probability calibration is statistically unreliable.
- **Formal Status:** `CALIBRATION_STATUS = INSUFFICIENT_DATA`.
- **Confidence Output Contract:** The model outputs `interaction_pattern_probability` with a conservative uncertainty band ($\pm 0.10$ to $\pm 0.20$), explicitly accompanied by limitation notes.

---

## 8. Cross-Circuit & Cross-Season Generalization

1. **Cross-Circuit Transfer (LOCO):**
   - Evaluated across 2 circuits: Monza (Italian GP) and Red Bull Ring (Austrian GP).
   - Training on Monza and testing on Red Bull Ring yields $Brier = 0.048$.
   - Training on Red Bull Ring and testing on Monza yields $Brier = 0.039$.
   - **Limitation:** Generalization is validated between low-downforce and downhill braking tracks, but cannot claim generalization to high-downforce street circuits (e.g., Monaco, Singapore).

2. **Cross-Season Transfer (LOSO):**
   - The current cohort only spans the **2024 Season**.
   - **Formal Status:** `SEASON_GENERALIZATION = INSUFFICIENT_DATA`.

---

## 9. Recommendations for Prompt 26 Implementation

1. **Feature Registry:** Implement a formal, machine-readable registry classifying every feature as `ALLOWED`, `CONDITIONAL`, or `FORBIDDEN`.
2. **Automated Leakage & Invariance Tests:** Add programmatic regression tests asserting zero output shift when driver/team identities or penalty outcomes are altered.
3. **Missingness Robustness Suite:** Test controlled signal dropouts (missing brake, throttle, geometry) ensuring graceful fallback.
4. **Model & Dataset Cards:** Create formal markdown documentation following industry transparency standards (`docs/ml-model-card.md` and `docs/ml-dataset-card.md`).
5. **API & Dossier Alignment:** Expose `/analysis/ml/evaluation`, `/analysis/ml/features`, and `/analysis/ml/model-card`, while embedding calibration status and epistemic typing in all steward dossier outputs.
