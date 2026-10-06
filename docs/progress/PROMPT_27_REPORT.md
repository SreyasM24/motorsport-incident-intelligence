# Prompt 27 — Evidence Quality, Uncertainty Propagation & Human Review Validation Report

**Repository:** `https://github.com/SreyasM24/motorsport-incident-intelligence.git`  
**Branch:** `main`  
**Status:** Complete & Verified  

---

## 1. Executive Summary

Prompt 27 reinforces the evidence foundation of the Motorsport Incident Intelligence platform by formalizing physical measurement uncertainty propagation, scientific numerical formatting, epistemic typing, and deterministic non-adjudicative steward inspection guidance.

Crucially:
- **Zero Autonomous Adjudication:** The system does not predict guilt, fault, liability, violation, or penalty recommendations.
- **Multidimensional Evidence Quality:** Strict adherence to `MULTIDIMENSIONAL_NO_AGGREGATE_SCORE`. No single universal scalar score is emitted, preventing false confidence in safety-critical incident analysis.
- **Physical Sensor Uncertainty:** Explicit propagation of hardware sensor limits ($\pm 0.20\text{ m}$ GPS, $\pm 0.28\text{ m}$ Euclidean gap, $\pm 2.0\text{ km/h}$ wheel speed, $\pm 0.040\text{ s}$ CAN bus epoch, $\pm 10.2\text{ m}$ clean reference lap braking delta).
- **Mathematical Distinguishability:** Discrepancies between evidence streams calculate combined uncertainty $\sigma_{\text{comb}} = \sqrt{\sigma_A^2 + \sigma_B^2}$ and evaluate whether differences exceed physical measurement noise.
- **Steward Review Focus:** Generates an empirical checklist of prioritized inspection targets without automated guilt or penalties.

---

## 2. Key Architecture & Implementation Deliverables

### 2.1 Scientific Numerical Formatting & Propagation Module
- **File:** `backend/app/evidence/formatting.py`
- Implemented:
  - `calculate_combined_uncertainty(sigma_a, sigma_b)`: Quadratic propagation $\sqrt{\sigma_a^2 + \sigma_b^2}$.
  - `is_statistically_distinguishable(difference, combined_uncertainty, tolerance_multiplier=1.0)`: Formulates rigorous hypothesis testing between sensor noise and physical anomaly.
  - `format_spatial_distance`, `format_velocity`, `format_time_delta`: Restricts output precision to avoid misleading false precision in judicial workflows.
  - `format_measurement_with_uncertainty`: Appends standardized `[±X.XX unit]` envelopes.

### 2.2 Canonical Contracts & Workspace Schemas
- **Files:** `backend/app/evidence/synthesis/contracts.py`, `backend/app/schemas/workspace.py`
- Added:
  - `EvidenceQualityLevel` (`HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`).
  - `EvidenceAvailabilityLevel` (`FULL`, `PARTIAL`, `LIMITED`, `UNAVAILABLE`).
  - `UncertaintySpecification` with physical bounds and epistemic categorization.
  - `combined_uncertainty`, `is_distinguishable`, and `significance_assessment` attributes on discrepancies.
  - `timestamp_uncertainty` and `spatial_uncertainty` attributes on timeline events.
  - `review_focus: List[str]` and `evidence_quality_matrix: Dict[str, Any]` on the workspace and dossier schemas.

### 2.3 Cross-Modal Consistency Engine Updates
- **File:** `backend/app/evidence/synthesis/consistency.py`
- Discrepancy detection now computes combined uncertainty:
  - Reference braking onset delta: Combined uncertainty $\pm 10.2\text{ m}$ ($\sqrt{2.0^2 + 10.0^2}$).
  - Apex overlap vs telemetry minimum gap: Combined uncertainty $\pm 0.34\text{ m}$ ($\sqrt{0.28^2 + 0.20^2}$).
  - Video synchronization vs telemetry: Combined temporal uncertainty $\pm 0.057\text{ s}$ ($\sqrt{0.040^2 + 0.040^2}$).

### 2.4 Steward Review Focus & Quality Matrix Service
- **File:** `backend/app/services/workspace_service.py`
- Implemented:
  - `_build_review_focus`: Formulates prioritized inspection items highlighting proximity within uncertainty bounds ($<1.0\text{ m}$ gap), unlinked commercial broadcast video, statistically distinguishable telemetry deviations, and prototype ML cohort limitations ($N=17$, calibration `INSUFFICIENT_DATA`).
  - `_build_evidence_quality_matrix`: Returns multidimensional matrix explicitly stamped with `"architecture_guarantee": "MULTIDIMENSIONAL_NO_AGGREGATE_SCORE"`.

### 2.5 API Endpoints
- **File:** `backend/app/api/workspace.py`
- Added:
  - `GET /api/v1/cases/{candidate_id}/review-focus`: Provides prioritized empirical inspection targets for stewards.
  - `GET /api/v1/cases/{candidate_id}/evidence-quality`: Exposes multidimensional quality, uncertainty, and availability data across evidence streams.

### 2.6 Frontend Workspace UI Enhancements
- **Files:**
  - `frontend/src/lib/types.ts`: Synchronized TypeScript interfaces.
  - `frontend/src/components/EvidenceTriagePanel.tsx`: Displays uncertainty envelopes (`±0.20m`, `±2.0 km/h`) and quality badge tags.
  - `frontend/src/components/DiscrepancyInvestigationPanel.tsx`: Displays combined uncertainty calculations and distinguishability badges (`DISTINGUISHABLE BEYOND UNCERTAINTY` vs `WITHIN UNCERTAINTY MARGIN`).
  - `frontend/src/views/IncidentDetailView.tsx`: Displays the non-adjudicative `STEWARD REVIEW FOCUS` checklist banner above the evidence panels.

---

## 3. Test & Verification Results

### 3.1 Evidence Quality Test Suite (`test_evidence_quality.py`)
16 targeted test cases executed and passed (100% pass rate):
1. `test_canonical_evidence_quality_schema`: Verified schema properties and type enforcement.
2. `test_epistemic_typing_strictness`: Verified `OBSERVED`, `DERIVED`, `MODEL_DERIVED`, `DOCUMENTARY`, `UNAVAILABLE`.
3. `test_quality_multidimensionality_no_scalar_score`: Verified rejection of scalar aggregate reliability score.
4. `test_measurement_uncertainty_vs_model_confidence_separation`: Verified strict separation of physical $\sigma$ and model $P(\hat{y}|x)$.
5. `test_numerical_precision_formatting`: Verified rounding and string formatting helpers.
6. `test_combined_uncertainty_calculation`: Verified quadratic error propagation.
7. `test_discrepancy_distinguishability_evaluation`: Verified statistical distinguishability thresholds.
8. `test_timeline_uncertainty_envelopes`: Verified timestamp and spatial uncertainty bounds on timeline events.
9. `test_deterministic_review_focus_generation`: Verified review focus generation across scenarios.
10. `test_review_focus_non_adjudicative_guardrails`: Adversarial check for absence of forbidden adjudicative terms (`fault`, `guilt`, `penalty`, `liable`, etc.).
11. `test_missing_evidence_creates_unbiased_review_focus`: Verified honest handling of unlinked broadcast footage.
12. `test_reference_baseline_uncertainty_propagation`: Verified baseline discrepancy uncertainty.
13. `test_ml_evidence_cohort_and_calibration_guardrails`: Verified $N=17$ cohort caveat and `INSUFFICIENT_DATA` calibration flag.
14. `test_real_reference_case_monza_01_uncertainty`: Full validation on REF-MONZA-01.
15. `test_real_reference_case_monza_02_and_03_uncertainty`: Full validation on REF-MONZA-02 and REF-MONZA-03.
16. `test_austria_red_bull_ring_uncertainty_and_api`: Full validation of workspace, `/review-focus`, and `/evidence-quality` API endpoints.

### 3.2 Frontend Compilation & Linting
- `npm run lint` (`tsc --noEmit`): **0 errors, 0 warnings**
- `npm run build` (`vite build`): **Build passed successfully**
