# Machine Learning Dataset Card: Multi-Circuit Incident & Nominal Racing Cohort

**Dataset Name:** `Multi-Circuit Incident Interaction Cohort`  
**Dataset Version:** `v1.1`  
**Schema Standard:** Prompt 26 ML Dataset Manifest Specification  
**Governing Standard:** Open Telemetry & FIA Official Document Corroboration  
**Scope:** 2024 Formula 1 World Championship (Italian Grand Prix & Austrian Grand Prix)  

---

## 1. Dataset Summary & Scientific Purpose

The dataset provides structured tabular observations of competitive vehicle-to-vehicle interactions in Formula 1 sessions. It is specifically designed to train and benchmark machine learning models that detect **anomalous physical interaction patterns** requiring human steward review, while benchmarking against **nominal racing maneuvers**.

> [!NOTE]
> **Data Authenticity & Copyright Boundary:**  
> All physical kinematic data is extracted from open CAN-bus telemetry and GPS timing feeds (FastF1/OpenF1). Commercial broadcast video footage is **NOT** included in this repository in compliance with Formula One Management (FOM) copyright protections.

---

## 2. Dataset Composition & Manifest Statistics

### Inventory Overview

| Category | Monza (Italian GP 2024) | Red Bull Ring (Austrian GP 2024) | Total Cohort Count |
| :--- | :--- | :--- | :--- |
| **Supervised Incident Candidates ($y=1$)** | 3 | 2 | **5** (29.4%) |
| **Supervised Nominal Controls ($y=0$)** | 7 | 5 | **12** (70.6%) |
| **Total Supervised Interactions ($N_{sup}$)** | 10 | 7 | **17** (100.0%) |
| **Excluded / Unverified Entries ($N_{excl}$)**| 1 (`AMBIG-MONZA-01`) | 1 (`AMBIG-AUSTRIA-01`) | **2** |
| **Total Manifest Records ($N_{total}$)** | 11 | 8 | **19** |

---

## 3. Data Sources & Provenance

1. **ECU CAN-bus & GPS Telemetry:**  
   Ingested through the FastF1 open-source library at 25Hz resampled SI units (speed, brake, throttle, RPM, Cartesian X/Y/Z).
2. **Official FIA Documents:**  
   Published steward decisions from the FIA portal (e.g., Monza Doc 54, Monza Doc 57, Austria Doc 66).
3. **Official FIA Race Control Messages:**  
   Time-stamped race control notifications and timing transponder feeds.

---

## 4. Inclusion & Exclusion Criteria

### Inclusion Criteria (`supervised_include = True`)
- Multi-car interactions with continuous telemetry coverage across approach, apex, and exit phases.
- Positive incidents corroborated by formal FIA Stewards Decisions or official Race Control notices.
- Negative controls representing clean passes or compliant side-by-side racing with zero car-to-car contact and zero track limits violations.

### Exclusion Criteria (`supervised_include = False`)
- Single-car track limits line-crossings without an interacting opponent (e.g., `AMBIG-MONZA-01`).
- Administrative or pit-exit blend infringements lacking dynamic vehicle interaction (e.g., `AMBIG-AUSTRIA-01`).
- Asynchronous sessions where transponder time offsets exceed 2.0 seconds.

---

## 5. Labeling Methodology

Every sample in the manifest includes authoritative provenance attributes:

```json
{
  "example_id": "REF-MONZA-01",
  "source_case_id": "REF-MONZA-01",
  "series": "Formula 1",
  "season": 2024,
  "event": "Italian Grand Prix",
  "circuit": "Monza",
  "session": "Race",
  "driver_identifiers": ["RIC", "HUL"],
  "label": 1,
  "label_source": "OFFICIAL_FIA_DOCUMENT",
  "label_confidence": 1.0,
  "evidence_available": ["telemetry", "baseline", "geometry"],
  "split_group": "monza_ric_hul_t8",
  "inclusion_status": "VERIFIED"
}
```

### Distinction Between Physical Label and Judicial Penalty
The target $y = 1$ reflects an **observable interaction anomaly**, not the penalty decision. A driver who locked brakes and forced another car wide exhibits $y = 1$ regardless of whether the stewards applied a 5-second penalty, a 10-second penalty, or decided No Further Action due to racing circumstances.

---

## 6. Circuit & Season Distributions

### Circuit Distribution
- **Autodromo Nazionale Monza:** High-speed circuit with heavy chicane braking and high top speeds. 10 supervised samples.
- **Red Bull Ring:** Short lap with heavy elevation changes and downhill braking into Turn 3 and Turn 4. 7 supervised samples.

### Season Distribution
- **2024 Season:** 100% of the active cohort. Cross-season evaluation is currently marked `SEASON_GENERALIZATION = INSUFFICIENT_DATA`.

---

## 7. Missing-Data & Sensor Noise Handling

- **Missing Brake or Throttle Sensors:** Unobserved sensor channels are set to default neutral values and paired with explicit boolean indicators (`missing_brake_flag = 1.0`).
- **Missing Baseline Laps:** If clean reference laps are unavailable (e.g. wet or safety car sessions), baseline deviation features default to 0.0 with `missing_baseline_flag = 1.0`.
- **GPS Jitter:** Filtered via central moving averages; residual positional uncertainty is documented at $\pm 0.20\text{ m}$.

---

## 8. Known Limitations & Scientific Boundaries

1. **Cohort Volume:** $N = 17$ supervised samples constitutes an **empirical prototype dataset**. It cannot support deep learning or large parameter counts without extreme overfitting.
2. **Class Imbalance:** 5 positive vs 12 negative samples (29.4% positive). Group-aware stratified evaluation is maintained.
3. **Synthetic Data Boundaries:** All tabular features are derived from genuine F1 session telemetry. No synthetic collisions or artificial driving traces are mixed into this supervised cohort.
