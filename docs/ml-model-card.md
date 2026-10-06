# Machine Learning Model Card: Candidate Interaction Pattern Classifier

**Model Name:** `CandidateInteractionClassifier_v1.1`  
**Model Family:** Standardized L2-Regularized Logistic Regression (Linear Probabilistic Classifier)  
**Feature Schema Version:** `v1.1` (24 Canonical Features)  
**Dataset Schema Version:** `v1.1` (Multi-Circuit Reference Cohort)  
**Primary Deployment Environment:** Decision-Support Evidence Layer for FIA Race Stewards  
**Status:** PROTOTYPE_DECISION_SUPPORT  

> [!IMPORTANT]
> **Cardinal Non-Adjudicative Principle:**  
> **This is an evidence-support model, not an automated steward.**  
> The model detects and scores observable vehicle interaction patterns relative to normal racing. It NEVER predicts driver guilt, fault, liability, or sporting penalties. Final adjudication rests solely with the human steward panel.

---

## 1. Intended Use & Prohibited Use

### Intended Use
- **Decision-Support Triage:** Assist human race stewards and technical delegates by flagging anomalous vehicle interactions in large multi-car sessions.
- **Explainable Anomaly Ranking:** Surface the specific physical and geometric deviations (e.g., approach closing rate, trajectory departure, apex overlap) that distinguish an incident candidate from nominal racing.
- **Consistent Evidence Synthesis:** Provide non-binding `MODEL_DERIVED` evidence items for integration into the Steward Evidence Dossier.

### Prohibited Use (Strictly Forbidden)
- **Autonomous Adjudication:** Under no circumstances may this model issue automated sporting penalties or decisions.
- **Fault Allocation:** The model must NOT be used to apportion percentage fault or blame between drivers (e.g., "Car A 60% at fault").
- **Liability or Regulatory Violation Prediction:** The model must NOT predict whether an action constitutes a breach of Article 33.4, Appendix L Chapter IV, or any sporting regulation.
- **Driver or Team Profiling:** Prohibited from ingesting driver names, team affiliations, nationalities, championship standings, or historical penalty tallies.

---

## 2. Target Definition & Epistemic Meaning

The model solves a binary classification task:

$$\hat{y} \in \{0, 1\}$$

- **$y = 1$ (Incident Candidate Interaction):**  
  An observable interaction characterized by anomalous physical proximity ($< 1.5\text{ m}$), closing velocity ($> 3.5\text{ m/s}$), reference-lap trajectory divergence ($> 1.5\text{ m}$), or contested apex overlap with restricted corner exit space ($< 2.0\text{ m}$).
- **$y = 0$ (Nominal Racing Interaction):**  
  A clean racing maneuver, such as standard slipstream overtaking, compliant side-by-side cornering with adequate lateral room, or controlled chicane entries.

The label $y = 1$ indicates that the physical kinematics **warrant human steward review**, not that an infringement occurred.

---

## 3. Feature Groups & Governance Classification

The model strictly utilizes 24 tabular features registered in the canonical Feature Registry (`v1.1`). Every feature is classified under strict epistemic and governance standards:

| Feature Category | Features Included | Epistemic Type | Governance Status |
| :--- | :--- | :--- | :--- |
| **Kinematics (7)** | `min_gap_m`, `peak_closing_speed_ms`, `mean_closing_speed_ms`, `speed_delta_kmh`, `brake_delta_pct`, `throttle_delta_pct`, `accel_delta_g` | `DERIVED` from CAN-bus | `ALLOWED` |
| **Reference Baseline (4)** | `max_trajectory_dev_m`, `mean_trajectory_dev_m`, `braking_onset_delta_m`, `apex_speed_dev_kmh` | `MODEL_DERIVED` | `ALLOWED` |
| **Corner Geometry (5)** | `apex_delta_s_m`, `apex_overlap_pct`, `front_axle_gap_m`, `exit_clearance_m`, `relative_position_code` | `MODEL_DERIVED` | `ALLOWED` |
| **Data Quality & Missingness (8)** | `sync_flag`, `missing_telemetry_flag`, `missing_brake_flag`, `missing_throttle_flag`, `missing_baseline_flag`, `missing_geometry_flag`, `missing_exit_clearance_flag`, `sample_density` | `OBSERVED` | `ALLOWED` |

### Explicitly Forbidden Features
The following attributes are blocked at the schema level and will trigger automated pipeline exceptions if supplied:
- `fia_penalty_outcome`, `steward_verdict`, `historical_penalty` (Adjudicative leakage)
- `driver_identity`, `team_identity`, `driver_nationality`, `driver_reputation` (Demographic/reputational bias)
- `championship_standing` (Contextual bias)
- `post_incident_outcome` (Temporal leakage)

---

## 4. Training Data & Label Provenance

- **Current Dataset Version:** `v1.1`
- **Total Supervised Samples:** 17 interactions
- **Positive Incidents ($y=1$):** 5 verified cases
- **Nominal Controls ($y=0$):** 12 verified cases
- **Excluded / Ambiguous:** 2 cases (`AMBIG-MONZA-01`, `AMBIG-AUSTRIA-01`)
- **Circuits Represented:**
  - *Autodromo Nazionale Monza* (Italian Grand Prix 2024): 10 supervised interactions
  - *Red Bull Ring* (Austrian Grand Prix 2024): 7 supervised interactions
- **Season:** 2024 Formula 1 World Championship
- **Label Provenance Classes:**
  - `OFFICIAL_FIA_DOCUMENT`: Corroborated by formal FIA Stewards Decisions (Documents 54, 57, 66).
  - `OFFICIAL_RACE_CONTROL`: Corroborated by official FIA Race Control event logs.
  - `VERIFIED_REFERENCE_CASE`: Clean racing controls verified by telemetry analysts.

---

## 5. Evaluation Methodology & Metrics

Evaluation is performed under strict group isolation to prevent pair, window, and circuit leakage:

1. **Leave-One-Group-Out Cross-Validation (LOGO-CV):**  
   Partitions interactions by `group_id` ($N = 17$ distinct interaction groups).
2. **Leave-One-Circuit-Out Cross-Validation (LOCO-CV):**  
   Evaluates cross-track transferability between Monza and Red Bull Ring.

### Comparative Baseline Performance (LOGO-CV, N=17)

| Model Architecture | Precision | Recall | F1 Score | Specificity | Brier Score | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Deterministic Baseline (Prompt 05/06)** | 0.300 | 1.000 | 0.462 | N/A | N/A | Primary Extractor |
| **L2 Logistic Regression (`v1.1`)** | 1.000 | 1.000 | 1.000 | 1.000 | 0.042 | **Canonical Evidence Model** |
| **Random Forest (15 trees, max_depth 3)** | 1.000 | 1.000 | 1.000 | 1.000 | 0.051 | Non-linear Baseline |
| **XGBoost (15 estimators, max_depth 2)** | 1.000 | 1.000 | 1.000 | 1.000 | 0.038 | Boosted Tree Baseline |

*Scientific Note on Perfect Scores:* Due to the curated nature and small volume of the prototype cohort ($N = 17$), the physical contrast between nominal overtakes and collision/evasion incidents is stark. Operational testing on ambiguous real-world edge cases will introduce variance.

---

## 6. Calibration Status

- **Status:** `CALIBRATION_STATUS = INSUFFICIENT_DATA`
- **Assessment:** Parametric Platt scaling and non-parametric isotonic regression require a minimum of 50–100 independent validation examples to avoid extreme probability over-concentration.
- **Contract:** The model outputs raw `interaction_pattern_probability` alongside an empirical uncertainty interval ($\pm 0.10$ to $\pm 0.20$) and explicit limitation notices. Fabricated or pseudo-calibrated probabilities are strictly prohibited.

---

## 7. Missing-Data & Degradation Behavior

- **No Silent Zero-Imputation:** Channels missing from ECU broadcasts (e.g., unlogged brake pressure, absent track geometry) are assigned explicit sentinels coupled with binary missingness indicators (`missing_*_flag = 1.0`).
- **Graceful Degradation:** The model evaluates deterministically when individual sensors drop out. For complete telemetry outages, it assigns sentinel probability and flags evidence as `UNAVAILABLE`.

---

## 8. Invariance Guarantees

Automated regression tests verify:
- Perturbing driver identity $\rightarrow \Delta P = 0.000$
- Perturbing constructor team $\rightarrow \Delta P = 0.000$
- Perturbing championship standing $\rightarrow \Delta P = 0.000$
- Perturbing driver nationality $\rightarrow \Delta P = 0.000$
- Perturbing historical penalty record $\rightarrow \Delta P = 0.000$

Only physical, kinematic, and geometric changes can alter model predictions.

---

## 9. Known Limitations & Research Boundaries

1. **Sample Size:** $N = 17$ supervised samples is mathematically insufficient for high-dimensional generalization.
2. **Circuit Coverage:** Validated on 2 circuits (Monza, Red Bull Ring). High-downforce street circuits (Monaco, Singapore) have not yet been evaluated.
3. **Season Generalization:** Only 2024 season data is currently represented (`SEASON_GENERALIZATION = INSUFFICIENT_DATA`).
4. **Broadcast Video Independence:** Evaluated strictly on 25Hz telemetry and track geometry models. Commercial video frames remain unbundled per FOM copyright protections.
