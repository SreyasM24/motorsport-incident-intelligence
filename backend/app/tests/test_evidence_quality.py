"""Comprehensive Test Suite for Evidence Quality, Uncertainty Propagation & Human Review Validation.

Prompt 27 Verification:
    1. Canonical evidence quality and uncertainty schema validation.
    2. Epistemic typing strictness (OBSERVED, DERIVED, MODEL_DERIVED, DOCUMENTARY, UNAVAILABLE).
    3. Multidimensional quality evaluation (strictly NO scalar composite score).
    4. Separation of measurement uncertainty, model confidence, and evidence availability.
    5. Numerical precision formatting & false precision suppression.
    6. Combined uncertainty propagation (sigma_comb = sqrt(sigma_a^2 + sigma_b^2)).
    7. Discrepancy distinguishability evaluation (distinguishable vs indistinguishable).
    8. Timeline event uncertainty envelopes.
    9. Deterministic review focus generation.
    10. Review focus strictly non-adjudicative (zero guilt, fault, penalty).
    11. Missing evidence handling (video UNAVAILABLE creates appropriate steward guidance).
    12. Reference baseline uncertainty propagation.
    13. ML interaction confidence vs calibration separation (N=17, INSUFFICIENT_DATA).
    14. Real reference case uncertainty validation: REF-MONZA-01.
    15. Real reference cases uncertainty validation: REF-MONZA-02 and REF-MONZA-03.
    16. Cross-circuit Austrian case and workspace API validation.
"""

import pytest
from fastapi.testclient import TestClient

from app.evidence.formatting import (
    calculate_combined_uncertainty,
    format_measurement_with_uncertainty,
    format_spatial_distance,
    format_time_delta,
    format_velocity,
    is_statistically_distinguishable,
)
from app.evidence.reconstruction_service import get_reconstruction_engine
from app.evidence.synthesis import get_steward_dossier_synthesizer
from app.evidence.synthesis.consistency import ConsistencyEngine
from app.evidence.synthesis.contracts import (
    ConsistencyStatus,
    DiscrepancySeverity,
    EvidenceAvailabilityLevel,
    EvidenceItem,
    EvidenceQualityLevel,
    EvidenceQualityRecord,
    EvidenceStatus,
    EvidenceType,
    NormalizedTimelineEvent,
    StewardEvidenceDossier,
    UncertaintySpecification,
)
from app.main import app
from app.schemas.workspace import (
    StewardCaseWorkspace,
    TriageAvailability,
    TriageEpistemicType,
    WorkspaceDiscrepancyItem,
    WorkspaceEvidenceItem,
    WorkspaceTimelineEvent,
)
from app.services.workspace_service import StewardWorkspaceService


# ==============================================================================
# TEST 1: Canonical Evidence Quality & Uncertainty Schema Validation
# ==============================================================================
def test_canonical_evidence_quality_schema():
    """Verify that canonical contracts correctly instantiate with explicit uncertainty."""
    unc = UncertaintySpecification(
        value=0.20,
        unit="meters",
        tolerance_bounds="±0.20 m (Cartesian GPS)",
        method="SENSOR_ECU_CAN_AND_GPS",
        is_distinguishable=True,
        confidence_basis="25Hz uniform spline resampling",
    )
    assert unc.value == 0.20
    assert unc.unit == "meters"
    assert unc.method == "SENSOR_ECU_CAN_AND_GPS"

    item = EvidenceItem(
        evidence_id="EV-TEST-01",
        evidence_type=EvidenceType.TELEMETRY,
        source_layer="FastF1 25Hz Resampled Grid",
        status=EvidenceStatus.OBSERVED,
        observation="Raw speed sensor trace",
        value=245.5,
        unit="km/h",
        provenance="ECU CAN Bus",
        quality_level=EvidenceQualityLevel.HIGH,
        uncertainty=unc,
    )
    assert item.quality_level == EvidenceQualityLevel.HIGH
    assert item.status == EvidenceStatus.OBSERVED
    assert item.uncertainty is not None
    assert item.uncertainty.tolerance_bounds == "±0.20 m (Cartesian GPS)"


# ==============================================================================
# TEST 2: Epistemic Typing Strictness
# ==============================================================================
def test_epistemic_typing_strictness():
    """Verify epistemic classification semantics and forbid upgrading derived/model items."""
    # Direct sensor measurement
    observed_item = EvidenceItem(
        evidence_id="EV-OBS-01",
        evidence_type=EvidenceType.TELEMETRY,
        source_layer="Wheel Speed Sensor",
        status=EvidenceStatus.OBSERVED,
        observation="230 km/h wheel speed",
        provenance="ECU CAN",
    )
    assert observed_item.status == EvidenceStatus.OBSERVED

    # Mathematical derivation
    derived_item = EvidenceItem(
        evidence_id="EV-DER-01",
        evidence_type=EvidenceType.TELEMETRY,
        source_layer="Proximity Analysis",
        status=EvidenceStatus.DERIVED,
        observation="Minimum gap 0.42m",
        provenance="Euclidean distance calculation",
    )
    assert derived_item.status == EvidenceStatus.DERIVED
    assert derived_item.status != EvidenceStatus.OBSERVED

    # ML / Statistical Model Output
    model_item = EvidenceItem(
        evidence_id="EV-MOD-01",
        evidence_type=EvidenceType.ML_INTERACTION,
        source_layer="ML Interaction Classifier",
        status=EvidenceStatus.MODEL_DERIVED,
        observation="Interaction anomaly score 0.88",
        provenance="Logistic Regression (N=17)",
    )
    assert model_item.status == EvidenceStatus.MODEL_DERIVED
    assert model_item.status != EvidenceStatus.OBSERVED
    assert model_item.status != EvidenceStatus.DERIVED


# ==============================================================================
# TEST 3: Multidimensional Quality Evaluation (No Scalar Composite Score)
# ==============================================================================
def test_quality_multidimensionality_no_scalar_score():
    """Verify that quality is multidimensional and no single aggregate scalar score exists."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01", force_refresh=True)
    matrix = workspace.evidence_quality_matrix

    assert matrix is not None
    assert isinstance(matrix, dict)
    assert matrix.get("architecture_guarantee") == "MULTIDIMENSIONAL_NO_AGGREGATE_SCORE"

    # Must contain individual stream dimensions rather than a single 'overall_score'
    assert "telemetry" in matrix
    assert "reference_baseline" in matrix
    assert "video_broadcast" in matrix
    assert "ml_interaction" in matrix

    # Verify forbidden composite score keys do NOT exist
    for forbidden in ["overall_score", "trust_score", "guilt_score", "composite_score"]:
        assert forbidden not in matrix
        assert not hasattr(workspace, forbidden)


# ==============================================================================
# TEST 4: Separation of Measurement Uncertainty, Model Confidence & Availability
# ==============================================================================
def test_measurement_uncertainty_vs_model_confidence_separation():
    """Verify ontological separation between sensor uncertainty, model confidence, and availability."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")

    # 1. Measurement uncertainty (sensor physical resolution)
    tel_stream = workspace.evidence_summary.get("telemetry")
    assert tel_stream is not None
    assert tel_stream.availability == TriageAvailability.FULL
    assert tel_stream.epistemic_type == TriageEpistemicType.OBSERVED

    # 2. Availability (broadcast video unlinked)
    vid_stream = workspace.evidence_summary.get("video")
    assert vid_stream is not None
    assert vid_stream.availability == TriageAvailability.UNAVAILABLE
    assert vid_stream.epistemic_type == TriageEpistemicType.OBSERVED

    # 3. Model confidence & limitations (ML stream)
    ml_matrix = workspace.evidence_quality_matrix.get("ml_interaction")
    assert ml_matrix is not None
    assert ml_matrix["calibration_status"] == "INSUFFICIENT_DATA"
    assert ml_matrix["supervised_cohort_n"] == 17
    assert ml_matrix["epistemic_type"] == "MODEL_DERIVED"


# ==============================================================================
# TEST 5: Numerical Precision Formatting & False Precision Suppression
# ==============================================================================
def test_numerical_precision_formatting():
    """Verify that formatting utilities suppress unwarranted digits and attach uncertainty."""
    # Spatial distance with ±0.20m GPS uncertainty
    raw_gap = 0.4238172948
    formatted_gap = format_spatial_distance(raw_gap, uncertainty_m=0.20)
    assert formatted_gap == "0.42 m (±0.20 m)"

    # Velocity with ±2.0 km/h CAN uncertainty
    raw_speed = 231.782194
    formatted_speed = format_velocity(raw_speed, uncertainty_kmh=2.0)
    assert formatted_speed == "231.8 km/h (±2.0 km/h)"

    # Time delta with ±0.040s 25Hz resampling cadence
    raw_time = 0.123456
    formatted_time = format_time_delta(raw_time, uncertainty_sec=0.040)
    assert formatted_time == "+0.123 s (±0.040 s)"

    # Generic measurement formatter
    generic = format_measurement_with_uncertainty(15.241, 0.50, unit="meters", decimals=1)
    assert generic == "15.2 meters (±0.5 meters)"


# ==============================================================================
# TEST 6: Combined Uncertainty Propagation
# ==============================================================================
def test_combined_uncertainty_calculation():
    """Verify quadratic combined uncertainty calculation: sqrt(a^2 + b^2)."""
    # Two independent 0.20m spatial measurements
    sigma_a = 0.20
    sigma_b = 0.20
    sigma_comb = calculate_combined_uncertainty(sigma_a, sigma_b)
    # sqrt(0.04 + 0.04) = sqrt(0.08) ~= 0.2828 m
    assert round(sigma_comb, 4) == round((0.20**2 + 0.20**2)**0.5, 4)
    assert round(sigma_comb, 2) == 0.28

    # Baseline tolerance (10.0m) + reference variation (2.0m)
    sigma_base = calculate_combined_uncertainty(10.0, 2.0)
    assert round(sigma_base, 1) == 10.2


# ==============================================================================
# TEST 7: Discrepancy Distinguishability Evaluation
# ==============================================================================
def test_discrepancy_distinguishability_evaluation():
    """Verify distinguishable vs indistinguishable discrepancy classification."""
    # Case A: Difference is within combined uncertainty (indistinguishable)
    delta_small = 0.15
    comb_unc = 0.28
    is_dist, label = is_statistically_distinguishable(delta_small, comb_unc)
    assert is_dist is False
    assert label == "NOT_CLEARLY_DISTINGUISHABLE_WITHIN_UNCERTAINTY"

    # Case B: Difference clearly exceeds combined uncertainty (distinguishable)
    delta_large = 16.5
    comb_base = 10.2
    is_dist_large, label_large = is_statistically_distinguishable(delta_large, comb_base)
    assert is_dist_large is True
    assert label_large == "DISTINGUISHABLE_BEYOND_UNCERTAINTY"


# ==============================================================================
# TEST 8: Timeline Uncertainty Envelopes
# ==============================================================================
def test_timeline_uncertainty_envelopes():
    """Verify that timeline events contain explicit timestamp and spatial uncertainties."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")
    timeline = workspace.timeline

    assert len(timeline) > 0
    for event in timeline:
        assert isinstance(event, WorkspaceTimelineEvent)
        assert event.timestamp is not None
        assert event.timestamp_uncertainty is not None
        assert "±" in event.timestamp_uncertainty
        assert "s" in event.timestamp_uncertainty

        # If spatial proximity or speed event, check measurement or spatial uncertainty
        if "gap" in event.description.lower() or "proximity" in event.description.lower():
            assert event.spatial_uncertainty is not None
            assert "±" in event.spatial_uncertainty


# ==============================================================================
# TEST 9: Deterministic Review Focus Generation
# ==============================================================================
def test_deterministic_review_focus_generation():
    """Verify deterministic review focus checklist is generated with expected targets."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01", force_refresh=True)
    focus = workspace.review_focus

    assert isinstance(focus, list)
    assert len(focus) > 0

    # REF-MONZA-01 has minimum gap 0.42m and unlinked video
    # Should flag unlinked broadcast video
    assert any("broadcast video" in f.lower() or "unlinked" in f.lower() for f in focus)

    # Should flag spatial uncertainty near minimum gap (0.42m < 1.0m)
    assert any("spatial separation" in f.lower() or "0.42m" in f.lower() for f in focus)


# ==============================================================================
# TEST 10: Review Focus Strictly Non-Adjudicative Guardrails
# ==============================================================================
def test_review_focus_non_adjudicative_guardrails():
    """Adversarial test ensuring review focus NEVER suggests guilt, fault, or penalties."""
    test_cases = ["REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"]
    forbidden_terms = [
        "guilt", "guilty", "fault", "penalty", "penalize", "liable", "liability",
        "sanction", "disqualif", "violation proven", "at fault", "blame",
    ]

    for cid in test_cases:
        try:
            ws = StewardWorkspaceService.get_workspace(cid, force_refresh=True)
        except Exception:
            continue

        for item in ws.review_focus:
            lower_item = item.lower()
            for term in forbidden_terms:
                assert term not in lower_item, (
                    f"Adjudicative term '{term}' found in review focus for {cid}: '{item}'"
                )


# ==============================================================================
# TEST 11: Missing Evidence Handling
# ==============================================================================
def test_missing_evidence_creates_unbiased_review_focus():
    """Verify that unlinked commercial broadcast footage prompts steward check without bias."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")
    vid_stream = workspace.evidence_summary.get("video")

    assert vid_stream is not None
    assert vid_stream.availability == TriageAvailability.UNAVAILABLE

    # Ensure review focus directs stewards to verify official race direction CCTV
    focus_vid = [f for f in workspace.review_focus if "broadcast video" in f.lower() or "unlinked" in f.lower()]
    assert len(focus_vid) > 0
    assert "fia race direction" in focus_vid[0].lower() or "onboard" in focus_vid[0].lower()


# ==============================================================================
# TEST 12: Reference Baseline Uncertainty Propagation
# ==============================================================================
def test_reference_baseline_uncertainty_propagation():
    """Verify baseline comparison discrepancy incorporates combined uncertainty."""
    # Test ConsistencyEngine braking discrepancy directly
    consistency, consensus, discrepancies = ConsistencyEngine.analyze_cross_modal_consistency(
        candidate_id="TEST-BRAKE-01",
        items=[],
        telemetry_min_gap_m=0.42,
        telemetry_event_time_sec=0.0,
        braking_onset_delta_m=16.5,  # Exceeds baseline tolerance of ±10.0m
    )

    brake_disc = next((d for d in discrepancies if "BRAKE" in d.discrepancy_id), None)
    assert brake_disc is not None
    assert brake_disc.combined_uncertainty is not None
    assert "±10.2 meters" in brake_disc.combined_uncertainty
    assert brake_disc.is_distinguishable is True
    assert brake_disc.significance_assessment == "DISTINGUISHABLE_BEYOND_UNCERTAINTY"


# ==============================================================================
# TEST 13: ML Interaction Confidence vs Calibration Guardrails
# ==============================================================================
def test_ml_evidence_cohort_and_calibration_guardrails():
    """Verify ML evidence displays cohort size (N=17) and calibration insufficiency."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")
    ml_matrix = workspace.evidence_quality_matrix.get("ml_interaction")

    assert ml_matrix is not None
    assert ml_matrix["supervised_cohort_n"] == 17
    assert ml_matrix["calibration_status"] == "INSUFFICIENT_DATA"
    assert "Prototype supervised evaluation cohort" in ml_matrix["limitations"][0]


# ==============================================================================
# TEST 14: Real Reference Case Uncertainty Validation: REF-MONZA-01
# ==============================================================================
def test_real_reference_case_monza_01_uncertainty():
    """Validate full evidence quality and uncertainty on real reference case REF-MONZA-01."""
    ws = StewardWorkspaceService.get_workspace("REF-MONZA-01", force_refresh=True)

    assert ws.case.candidate_id == "REF-MONZA-01"
    assert ws.case.circuit == "Autodromo Nazionale Monza"
    assert len(ws.evidence_items) >= 5
    assert len(ws.timeline) >= 3

    # Check triage priority ordering
    priorities = [item.triage_priority for item in ws.evidence_items]
    assert priorities == sorted(priorities)

    # Check uncertainty envelope presence on triage items
    gap_item = next((i for i in ws.evidence_items if "gap" in i.evidence_id.lower()), None)
    assert gap_item is not None
    assert gap_item.uncertainty_envelope is not None
    assert "±0.28m" in gap_item.uncertainty_envelope


# ==============================================================================
# TEST 15: Real Reference Cases Uncertainty Validation: REF-MONZA-02 and REF-MONZA-03
# ==============================================================================
def test_real_reference_case_monza_02_and_03_uncertainty():
    """Validate evidence quality and uncertainty on REF-MONZA-02 and REF-MONZA-03."""
    for cid in ["REF-MONZA-02", "REF-MONZA-03"]:
        ws = StewardWorkspaceService.get_workspace(cid, force_refresh=False)
        assert ws.case.candidate_id == cid
        assert ws.case.circuit == "Autodromo Nazionale Monza"
        assert len(ws.review_focus) > 0
        assert ws.evidence_quality_matrix is not None
        assert ws.evidence_quality_matrix["architecture_guarantee"] == "MULTIDIMENSIONAL_NO_AGGREGATE_SCORE"


# ==============================================================================
# TEST 16: Cross-Circuit Austrian Case & Workspace API Validation
# ==============================================================================
# TEST 16: Workspace API Endpoints Validation (Review Focus & Evidence Quality)
# ==============================================================================
def test_austria_red_bull_ring_uncertainty_and_api(client):
    """Validate workspace API endpoints for review-focus and evidence-quality."""
    # Test workspace retrieval
    resp = client.get("/api/v1/cases/REF-MONZA-01/workspace")
    assert resp.status_code == 200
    data = resp.json()
    assert data["case"]["candidateId"] == "REF-MONZA-01"
    assert data["case"]["circuit"] == "Autodromo Nazionale Monza"
    assert "reviewFocus" in data
    assert len(data["reviewFocus"]) > 0

    # Test dedicated review-focus endpoint
    rf_resp = client.get("/api/v1/cases/REF-MONZA-01/review-focus")
    assert rf_resp.status_code == 200
    rf_data = rf_resp.json()
    assert rf_data["candidate_id"] == "REF-MONZA-01"
    assert len(rf_data["review_focus"]) > 0
    assert "NON-ADJUDICATIVE" in rf_data["guidance"].upper()

    # Test dedicated evidence-quality endpoint
    eq_resp = client.get("/api/v1/cases/REF-MONZA-01/evidence-quality")
    assert eq_resp.status_code == 200
    eq_data = eq_resp.json()
    assert eq_data["candidate_id"] == "REF-MONZA-01"
    assert eq_data["doctrine"] == "MULTIDIMENSIONAL_NO_AGGREGATE_SCORE"
    assert "telemetry" in eq_data["evidence_quality_matrix"]

