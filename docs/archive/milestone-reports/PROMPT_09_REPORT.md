# PROMPT 09 PROGRESS REPORT: CORNERING OVERTAKE GEOMETRY & APEX OVERLAP ANALYSIS

**Date:** 2026-09-27  
**Status:** PASS  
**Full Test Suite:** 99 passed, 0 failed (310.63s)  
**Prompt 09 Suite:** 13 passed, 0 failed (33.29s)  
**Frontend Typecheck (`npm run lint`):** Clean (0 errors, 0 warnings)  
**Frontend Production Build (`npm run build`):** Clean (Exit Code 0, built in 17.43s)  
**Database (PostgreSQL):** Locally unavailable and honestly reported as unverified (SQLite test/dev fallback verified)

---

## 1. Executive Summary

Prompt 09 completes the implementation of a deterministic, physically grounded **Cornering Overtake Geometry & Apex Overlap Analysis** layer within the Motorsport Incident Intelligence platform. Building on top of Prompt 08's reference-lap trajectory deviations, this module quantitatively evaluates the relative spatial ordering, longitudinal overlap, front-axle displacement, and corner exit room between interacting cars throughout the cornering progression (Entry $\to$ Braking Onset $\to$ Turn-In $\to$ Apex $\to$ Exit).

### Strict Jurisprudential Guardrails Maintained
1. **Empirical Measurements Only**: The engine outputs purely factual quantities ($\Delta s$ in meters, $\Delta t$ in seconds, overlap percentage against $5.63\text{m}$ reference length, and exit clearance against $2.00\text{m}$ reference car width).
2. **Zero Automated Adjudication**: Under no circumstance does this module output fault, guilt, penalty recommendations, or declare an overtake "legal" or "illegal".
3. **Explicit Provenance**: Every metric reports its sensor provenance (`DIRECTLY_OBSERVED`, `DERIVED_FROM_TELEMETRY`, `DERIVED_FROM_POSITION`, `PARTIALLY_OBSERVABLE`, or `UNAVAILABLE`).
4. **No Synthetic Track Limits**: Where curvilinear track edge survey data is absent, the system explicitly reports exit clearance as vehicle spatial clearance and flags track boundary limits as `UNAVAILABLE` rather than hallucinating boundaries.

---

## 2. Mathematical & Geometric Formulations

### A. Coordinate Framework
- **Invariant Metric Axis**: Normalized track distance $s$ (meters) along the racing trajectory.
- **Cartesian Spatial Grid**: FastF1 coordinate decimeter-to-meter scaling ($X/10.0, Y/10.0, Z/10.0$) preserved across all 2D distance computations.
- **Reference Vehicle Dimensions**:
  - Maximum Regulation Vehicle Length: $L_{\text{ref}} = 5.63\text{ m}$
  - Maximum Regulation Vehicle Width: $W_{\text{ref}} = 2.00\text{ m}$
  - Front-Axle-to-Mirror Longitudinal Offset: $D_{\text{mirror}} = 2.20\text{ m}$

### B. Longitudinal Spacing & Ordering
$$\Delta s = s_{\text{incident}} - s_{\text{other}} \quad (\text{meters})$$
$$\Delta t = \frac{\Delta s}{\bar{v}} \quad (\text{seconds}), \quad \bar{v} = \max\left(\frac{v_a + v_b}{2}, 10.0\text{ m/s}\right)$$

Physical ordering is classified purely based on $\Delta s$:
- $\Delta s > +0.50\text{ m} \implies \text{AHEAD}$
- $\Delta s < -0.50\text{ m} \implies \text{BEHIND}$
- $|\Delta s| \le 0.50\text{ m} \implies \text{APPROXIMATELY\_ALONGSIDE}$

### C. Longitudinal & Front-Axle Overlap
$$\text{overlap\_length} = \max(0.0, L_{\text{ref}} - |\Delta s|)$$
$$\text{overlap\_percent} = \min\left(100.0, \frac{\text{overlap\_length}}{L_{\text{ref}}} \times 100.0\right)$$

Categorization aligns directly with FIA Driving Standards Guidelines references:
- $|\Delta s| \ge 5.63\text{m} \implies \text{NO\_MEASURABLE\_OVERLAP}$ ($0.0\%$)
- $0.0\% < \text{overlap} < 45.0\% \implies \text{PARTIAL\_OVERLAP}$
- $45.0\% \le \text{overlap} \le 55.0\% \implies \text{APPROXIMATELY\_50\_PERCENT\_OVERLAP}$
- $\text{overlap} > 55.0\% \implies \text{GREATER\_THAN\_50\_PERCENT\_OVERLAP}$

### D. Corner Exit Clearance
$$\text{Clearance} = \text{lateral\_dist\_meters} \quad (\text{or } 2\text{D Euclidean gap})$$
Evaluated against the $2.00\text{m}$ one-car-width engineering standard:
- $\text{Clearance} \ge 2.10\text{ m} \implies \text{CLEARANCE\_ABOVE\_REFERENCE}$
- $1.90\text{ m} \le \text{Clearance} < 2.10\text{ m} \implies \text{CLEARANCE\_NEAR\_REFERENCE}$
- $\text{Clearance} < 1.90\text{ m} \implies \text{CLEARANCE\_BELOW\_REFERENCE}$
- Exit unreached or missing channels $\implies \text{CLEARANCE\_UNAVAILABLE}$

---

## 3. Architecture & Code Changes

### A. Backend Schemas & Domain Models
- [`backend/app/schemas/overtake_geometry.py`](backend/app/schemas/overtake_geometry.py):
  - Enums: `MeasurementConfidence`, `RelativeLongitudinalPosition`, `OverlapClassification`, `ExitClearanceClassification`.
  - Pydantic models: `CornerPhaseSnapshot`, `ApexOverlapSnapshot`, `CornerPhases`, `ExitClearanceMetrics`, `FIAGuidelineReference`, `OvertakeGeometryDataQuality`, `OvertakeGeometryEvidence`.
- [`backend/app/evidence/overtake_geometry_models.py`](backend/app/evidence/overtake_geometry_models.py):
  - Clean re-export interface avoiding circular imports between `app.schemas` and `app.evidence`.

### B. Core Calculation Service
- [`backend/app/services/overtake_geometry_service.py`](backend/app/services/overtake_geometry_service.py):
  - `CorneringOvertakeGeometryService` with singleton accessor `get_overtake_geometry_service()`.
  - Robust `_extract_distance()` helper handling missing distance channels via numerical speed integration over time offsets.
  - `detect_corner_phases()`: Apex detection at minimum corner speed landmark, entry at deceleration/braking onset, exit at throttle recovery.
  - `calculate_vehicle_relationship()`: Evaluates $\Delta s$, $\Delta t$, and physical ordering.
  - `calculate_overlap()`: Evaluates front axle displacement and vehicle body overlap against $5.63\text{m}$ reference.
  - `calculate_apex_snapshot()`: Apex frame spatial snapshot with front-axle gap and mirror overlap reference ($2.20\text{m}$).
  - `calculate_exit_clearance()`: Corner exit room vs $2.00\text{m}$ regulation car width reference.
  - `build_phase_snapshots()`: Generates chronological progression table across 7 milestones (`ENTRY`, `BRAKING_ONSET`, `TURN_IN`, `APEX`, `APEX+10M`, `APEX+20M`, `EXIT`).
  - `synthesize_overtake_geometry()`: End-to-end evidence synthesis.

### C. Evidence Dossier & API Integration
- [`backend/app/evidence/dossier.py`](backend/app/evidence/dossier.py):
  - Added `overtake_geometry: Optional[OvertakeGeometryEvidence]` to `IncidentEvidenceDossier` and `IncidentDetailResponse`.
  - Automated overtake geometry synthesis when telemetry frames are available.
  - Added `GEOMETRY` category evidence items (`Apex Overlap & Proximity`, `Corner Exit Lateral Clearance`) to `convert_dossier_to_frontend_incident()`.
- [`backend/app/api/analysis.py`](backend/app/api/analysis.py):
  - Added `GET /api/v1/analysis/candidates/{candidate_id}/overtake-geometry`.
  - Updated `/frontend-incident` endpoint to include `overtakeGeometry` payload.

### D. Frontend Presentation
- [`src/lib/types.ts`](src/lib/types.ts):
  - Added TypeScript definitions for all Overtake Geometry types and added `'GEOMETRY'` to `EvidenceCategory`.
- [`src/components/OvertakeGeometryPanel.tsx`](src/components/OvertakeGeometryPanel.tsx):
  - High-level classification status badge.
  - Steward jurisprudential notice reminding reviewers that metrics are empirical and non-binding.
  - 3 Core Geometric Snapshot cards: Apex Longitudinal Overlap, Exit Lateral Clearance, Corner Phase Landmarks.
  - Milestone Progression Snapshots table tracking $\Delta s$, speeds, and positions across the corner.
  - Normative FIA Driving Standards Guidelines references and Data Quality indicators.
- [`src/views/IncidentDetailView.tsx`](src/views/IncidentDetailView.tsx):
  - Rendered `OvertakeGeometryPanel` under Section 4C (`4C. CORNERING OVERTAKE GEOMETRY & APEX OVERLAP`).

---

## 4. Verification & Test Results

### Dedicated Prompt 09 Suite (`test_overtake_geometry.py`)
13 passed out of 13 tests in 33.29s:
1. `test_no_measurable_overlap`: Gap $\ge 5.63\text{m} \implies 0.0\%$ overlap, `NO_MEASURABLE_OVERLAP`.
2. `test_partial_overlap`: Gap $4.0\text{m} \implies 28.9\%$ overlap, `PARTIAL_OVERLAP`.
3. `test_approximately_50_percent_overlap`: Gap $2.815\text{m} \implies 50.0\%$ overlap, `APPROXIMATELY_50_PERCENT_OVERLAP`.
4. `test_greater_than_50_percent_overlap`: Gap $1.0\text{m} \implies 82.2\%$ overlap, `GREATER_THAN_50_PERCENT_OVERLAP`.
5. `test_perfect_alignment_full_overlap`: Gap $0.0\text{m} \implies 100.0\%$ overlap.
6. `test_relative_longitudinal_ordering`: Evaluates `AHEAD`, `BEHIND`, and `APPROXIMATELY_ALONGSIDE`.
7. `test_corner_phase_detection`: Apex detected at minimum speed landmark, exit at throttle recovery.
8. `test_exit_clearance_metrics`: Evaluates $2.5\text{m}$ (`CLEARANCE_ABOVE_REFERENCE`), $2.0\text{m}$ (`CLEARANCE_NEAR_REFERENCE`), and $1.4\text{m}$ (`CLEARANCE_BELOW_REFERENCE`).
9. `test_missing_positional_coordinates_graceful_fallback`: Missing/zero coordinates fallback to `INSUFFICIENT_GEOMETRIC_DATA` without crashing.
10. `test_empty_frames_handling`: Empty frame list handled gracefully.
11. `test_end_to_end_synthesis`: Candidate synthesis populates phases, apex snapshot, clearance, and milestones.
12. `test_api_overtake_geometry_endpoint`: Real Monza FastF1 candidate query via `GET /api/v1/analysis/candidates/REF-MONZA-01/overtake-geometry`.
13. `test_api_frontend_incident_includes_overtake_geometry`: Verified that `/frontend-incident` includes `overtakeGeometry` and `GEOMETRY` category evidence items.

### Full Test Suite Regression Check
```
================= 99 passed, 92 warnings in 310.63s (0:05:10) =================
```
- Total tests: 99 passed, 0 failed.
- Zero regressions across candidate detection, FastF1 ingestion, baseline quantification, and human review workflow.

---

## 5. Recommended Next Step (Prompt 10)

With Prompt 09 complete, the incident intelligence engine possesses both baseline trajectory deviations (Prompt 08) and cornering overtake geometry (Prompt 09). The natural architectural progression is:
**PROMPT 10 — FIA DRIVING STANDARDS GUIDELINE COMPLIANCE ENGINE & STEWARD DOSSIER SYNTHESIS**:
- Codify explicit, rule-based algorithmic mapping against FIA Driving Standards Guidelines (Inside Overtake, Outside Overtake, Chicane Apex Entitlement, and Forcing Off Track).
- Generate structured steward deliberation briefs cross-referencing Prompt 08 trajectory disruptions, Prompt 09 overlap ratios, race control messages, and relevant sporting regulation articles.
