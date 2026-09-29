# Historical Motorsport Incident Reconstruction Benchmark (MII-HIRB-v1.1)

**Suite Version:** `1.1.0` (Expanded Multi-Circuit / Multi-Season with Provenance Audit)  
**Manifest:** [`data/benchmarks/historical_incidents/historical_incidents_v1.json`](../../data/benchmarks/historical_incidents/historical_incidents_v1.json)  
**Provenance Matrix:** [`docs/evaluation/benchmark_provenance_matrix.md`](benchmark_provenance_matrix.md)  
**Evaluation Target:** Evidence Reconstruction Quality, Group-Aware Generalization & Epistemic Purity  
**Evaluation Scope:** 30 Verified Historical Cases across 8 Circuits & 2 Seasons (2023–2024)

---

## 1. Executive Summary & Epistemic Guardrails

The **Historical Motorsport Incident Reconstruction Benchmark (MII-HIRB-v1.1)** evaluates the performance of the Motorsport Incident Intelligence platform in reconstructing historically documented racing interactions into evidence dossiers suitable for licensed human steward review.

> [!IMPORTANT]
> **CRITICAL ARCHITECTURAL BOUNDARY: NO FAULT OR PENALTY PREDICTION**
> 
> MII-HIRB-v1.1 evaluates **EVIDENCE RECONSTRUCTION QUALITY & PROVENANCE INTEGRITY**.
> - It is **NOT** a fault classification benchmark.
> - It is **NOT** a guilt prediction benchmark.
> - It is **NOT** a penalty recommendation benchmark.
> 
> Historical steward decisions (fines, grid penalties, time penalties) are treated strictly as **DOCUMENTARY EVIDENCE**. They do not constitute physical ground truth or supervised training labels for guilt.

---

## 2. Benchmark Independence & Provenance Audit Summary

To prevent circular evaluation, every metric in the benchmark suite was audited for ground-truth independence:

- **Independently Grounded Metrics:**
  - *Reference Baseline Selection Correctness*: Validates deterministic exclusion of contaminated laps against official session logs.
  - *Regulatory Context Retrieval*: Evaluates semantic retrieval of Sporting Code articles against official citations.
  - *Epistemic Typing Compliance*: Enforces zero illegal type upgrades (`MODEL_DERIVED` or `DOCUMENTARY` $\to$ `OBSERVED`).
  - *Lineage Deduplication*: Prevents double-counting by tracking root physical sensors via `LineageTracker`.
  - *Cross-Modal Consistency*: Quantifies cross-stream divergence (telemetry vs. driver claim vs. video).
- **Telemetry-Derived Consistency Checks (Reclassified):**
  - *Temporal Reconstruction*: Reclassified from "independent accuracy" to **Telemetry-Derived Temporal Consistency Check** ($IoU \ge 0.50$, error $\le 2.0\text{ s}$). Both ground truth and reconstruction share the CAN-bus session clock.
  - *Vehicle Association*: Reclassified to **Identifier Propagation Correctness**. Independent visual identification is marked **`INSUFFICIENT_DATA`** due to broadcast copyright limitations.
  - *Spatial & Kinematics*: Reclassified to **Spatial Reconstruction Consistency**. Verifies physical plausibility within defined CAN-bus boundaries.

*Full details and per-dimension justifications are recorded in the [Benchmark Provenance Matrix](benchmark_provenance_matrix.md).*

---

## 3. Dataset Composition & Verified Cohort

The benchmark incorporates 32 total curated cases spanning 8 distinct circuits and 2 Formula 1 seasons:

```
Total Cases in Manifest: 32
├── Verified Quantitative Cases: 30
│   ├── Documented Racing Incidents: 18
│   └── Nominal Racing Controls: 12
└── Unverified Excluded Cases: 2 (Strictly excluded from quantitative scoring)
```

### Circuit & Season Distribution

- **Circuits (8):** Autódromo Hermanos Rodríguez (Mexico), Circuit of the Americas (USA), Las Vegas Strip Circuit (USA), Losail International Circuit (Qatar), Monza (Italy), Red Bull Ring (Austria), Spa-Francorchamps (Belgium), Yas Marina Circuit (UAE).
- **Seasons (2):** 2023 (8 verified cases) and 2024 (22 verified cases).
- **Nominal Controls (12):** Covering normal following, DRS highway passing, close corner entry/exit, apex defense, and multi-car tow dynamics.
- **Unverified Controls (2):** `HIST-2024-SILVERSTONE-UNVERIFIED-01` and `HIST-2023-MONACO-UNVERIFIED-02` (unverified paddock rumors strictly excluded from quantitative scoring).

---

## 4. Multi-Dimensional Decoupled Benchmark Results

In strict adherence to scientific integrity, **zero composite scores (e.g., "MII Accuracy = 94%") are computed**. Each evaluation dimension is reported independently:

### Suite-Level Results (N = 30 Verified Cases)

| Evaluation Dimension | Primary Metric | Observed Result | Target Benchmark | Benchmark Status |
| :--- | :--- | :---: | :---: | :---: |
| **1. Temporal Alignment** | Telemetry Temporal Consistency Rate | **100.0%** | $\ge 85.0\%$ | **PASS (Consistency)** |
| | Mean Absolute Error ($MAE$) | **0.00 s** | $\le 1.0\text{ s}$ | **PASS** |
| | Mean Window IoU | **1.00** | $\ge 0.70$ | **PASS** |
| **2. Vehicle Association** | Identifier Propagation Accuracy | **100.0%** | $\ge 90.0\%$ | **PASS (Propagation)** |
| | Independent Visual Identity | *INSUFFICIENT_DATA* | N/A | **DOCUMENTED** |
| **3. Spatial & Kinematics** | Spatial Reconstruction Consistency | **100.0%** | $100.0\%$ | **PASS (Consistency)** |
| **4. Reference Lap Baseline** | Clean Baseline Validity Rate | **93.3%** | $\ge 70.0\%$ | **PASS (Honest)** |
| **5. Regulatory Retrieval** | Statutory Article Recall | **100.0%** | $\ge 80.0\%$ | **PASS (Independent)** |
| | Statutory Article Precision | **100.0%** | $\ge 75.0\%$ | **PASS (Independent)** |
| | Epistemic Documentary Purity | **100.0%** | $100.0\%$ | **PASS (Independent)** |
| **6. Epistemic Typing** | Taxonomy Compliance Pass Rate | **100.0%** | $100.0\%$ | **PASS (Independent)** |
| **7. Evidence Lineage** | Double-Counting Prevention Rate | **100.0%** | $100.0\%$ | **PASS (Independent)** |
| | Mean Naive Metrics vs. Root Sources | **4.00 vs 2.00** | Root < Naive | **PASS (Independent)** |
| **8. Cross-Modal Alignment** | Alignment Validity Pass Rate | **100.0%** | $\ge 90.0\%$ | **PASS (Independent)** |

> [!NOTE]
> **Baseline Validity Rate (93.3%) Analysis**: Opening lap incidents (such as `HIST-2024-ITA-R-02` and `HIST-2023-QAT-R-01`) naturally lack preceding green-flag laps in their stint. MII honestly returns `INSUFFICIENT_REFERENCE_DATA` rather than synthesizing an artificial baseline.

---

## 5. Group-Aware Cross-Validation Partitions

To verify that reconstruction heuristics do not leak data across sessions or tracks, MII implements Leave-One-Circuit-Out (LOCO) and Leave-One-Season-Out (LOSO) partitioning:

### Leave-One-Circuit-Out (LOCO) Consistency

| Holdout Circuit | Test Cases ($N$) | Temporal Consistency | Spatial Consistency | Baseline Validity |
| :--- | :---: | :---: | :---: | :---: |
| **Monza** | 6 | 100.0% | 100.0% | 83.3% |
| **Red Bull Ring** | 4 | 100.0% | 100.0% | 100.0% |
| **Circuit of the Americas** | 5 | 100.0% | 100.0% | 100.0% |
| **Autódromo Hermanos Rodríguez** | 5 | 100.0% | 100.0% | 100.0% |
| **Spa-Francorchamps** | 3 | 100.0% | 100.0% | 100.0% |
| **Las Vegas Strip Circuit** | 3 | 100.0% | 100.0% | 100.0% |
| **Yas Marina Circuit** | 2 | 100.0% | 100.0% | 100.0% |
| **Losail International Circuit** | 2 | 100.0% | 100.0% | 50.0% |

### Leave-One-Season-Out (LOSO) Consistency

| Holdout Season | Test Cases ($N$) | Temporal Consistency | Spatial Consistency | Baseline Validity |
| :--- | :---: | :---: | :---: | :---: |
| **2023 Season** | 8 | 100.0% | 100.0% | 87.5% |
| **2024 Season** | 22 | 100.0% | 100.0% | 95.5% |

---

## 6. Historical Case Comparator Evaluation

The observable case comparator was audited to verify that case matching is strictly geometric and kinematic:

```
Comparator Feature Isolation Audit: VERIFIED_PASS
Disallowed Features Checked:
  - steward_decision_type (None)
  - penalty_points (None)
  - time_penalty_seconds (None)
  - driver_reputation (None)
  - championship_standing (None)
  - fault_allocation_ratio (None)

Allowed Observable Features Used:
  - interaction_category (0.40 weight)
  - corner_phase (0.20 weight)
  - minimum_gap_meters_range (0.20 weight)
  - delta_brake_meters_range (0.20 weight)
```

### Empirical Retrieval Performance (Top-3 Matches across N = 30 Queries)

- **Non-Precedent Isolation:** **100% Pass** (Zero penalty/ruling influence)
- **Observable Category Congruence:** **91.1%**
- **Mean Gap Proximity Error:** **0.49 meters**
- **Mean Braking Delta Error:** **2.43 meters**

---

## 7. Failure Mode Taxonomy & Distribution

Reconstruction anomalies across all cases are categorized under the formal 11-mode taxonomy:

```
Failure Mode Counts (32 Total Cases):
├── NONE: 28 (Clean reconstruction meeting all tolerances)
├── BASELINE_SELECTION: 2 (Lap 1 stint starts; insufficient prior green-flag laps)
└── DATA_UNAVAILABLE: 2 (Unverified negative controls strictly excluded)
```

---

## 8. REST API Endpoints

The expanded benchmark suite is fully integrated and accessible via the API:

- `GET /api/v1/analysis/benchmark/historical-incidents`: Returns the complete `BenchmarkSuiteReport` including reclassified dimensions and split summaries.
- `GET /api/v1/analysis/benchmark/provenance-matrix`: Returns the formal 9-dimension Ground Truth vs System Source matrix.
- `GET /api/v1/analysis/benchmark/splits?split_type=circuit|season|event`: Returns partition lists with zero cross-split leakage.
- `GET /api/v1/analysis/benchmark/comparator-evaluation`: Returns feature isolation proof and physical retrieval metrics.
