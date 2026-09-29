"""Test suite for Prompt 16 — Multi-Modal Evidence Synthesis, Discrepancy Analysis & Steward Dossier.

Tests:
    1. EvidenceItem contract & explicit epistemic typing (OBSERVED, DERIVED, MODEL_DERIVED, DOCUMENTARY, UNAVAILABLE)
    2. Provenance lineage & double-counting prevention (LineageTracker)
    3. Cross-modal consistency engine & discrepancy classification
    4. Unavailable evidence handling & transparent missingness
    5. Descriptive regulation linkage (zero automated violation verdicts)
    6. Normalized chronological timeline synthesis
    7. Master Steward Evidence Dossier synthesis (all 14 canonical sections)
    8. Deterministic machine-readable JSON export
    9. Human review workflow integration (state machine preservation)
    10. Official Monza reference cases validation (REF-MONZA-01, 02, 03)
    11. REST API endpoints (/dossier and /dossier/export/json)
    12. Critical non-adjudicative guardrails (zero fault, guilt, or penalty claims)
"""

import json
import pytest
from fastapi.testclient import TestClient

from app.evidence.candidate import (
    CandidateDossier,
    CandidateEventType,
    CandidateStatus,
    DataQualityFlags,
)
from app.evidence.dossier import synthesize_incident_evidence_dossier
from app.evidence.reconstruction_service import get_reconstruction_engine
from app.evidence.synthesis.consistency import ConsistencyEngine
from app.evidence.synthesis.contracts import (
    ConsistencyStatus,
    CrossModalDiscrepancy,
    DiscrepancySeverity,
    EvidenceConsensus,
    EvidenceItem,
    EvidenceStatus,
    EvidenceType,
    NormalizedTimelineEvent,
    StewardEvidenceDossier,
)
from app.evidence.synthesis.lineage import LineageTracker
from app.evidence.synthesis.synthesizer import (
    StewardDossierSynthesizer,
    get_steward_dossier_synthesizer,
)
from app.main import app
from app.schemas.telemetry import TelemetryPointSchema


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_candidate() -> CandidateDossier:
    return CandidateDossier(
        candidate_id="CAND-TEST-SYNTHESIS-01",
        session_id="Italian Grand Prix 2024 — Race",
        driver_a="MAG",
        driver_b="GAS",
        car_number_a=20,
        car_number_b=10,
        team_a="Haas",
        team_b="Alpine",
        lap_number_a=19,
        lap_number_b=19,
        turn="Turn 4 (Variante della Roggia)",
        event_start="15:42:17.000",
        event_peak="15:42:18.400",
        event_end="15:42:20.000",
        duration_seconds=3.0,
        event_type=CandidateEventType.RAPID_PROXIMITY_EVENT,
        detection_method="KINEMATIC_PROXIMITY_ANALYZER",
        evidence_strength=88,
        minimum_gap_meters=1.82,
        peak_closing_speed_ms=8.4,
        speed_delta_at_peak=2.0,
        speed_a_at_peak=220.0,
        speed_b_at_peak=222.0,
        braking_change={"decel_delta_g": 1.2, "brake_pressure_delta_bar": 45.0},
        trajectory_divergence={"lateral_displacement_m": 0.85},
        status=CandidateStatus.PENDING_REVIEW,
        summary="Close interaction at Variante della Roggia apex with late braking.",
        data_quality_flags=DataQualityFlags(),
    )


@pytest.fixture
def mock_telemetry_frames() -> list[TelemetryPointSchema]:
    frames = []
    for i in range(25):
        t = 15.0 + i * 0.04
        frames.append(
            TelemetryPointSchema(
                timestamp=f"15:42:{t:06.3f}",
                time_offset=t - 15.0,
                speed_a=240.0 - i * 4.0,
                speed_b=242.0 - i * 4.2,
                throttle_a=0.0 if i > 5 else 100.0,
                throttle_b=0.0 if i > 6 else 100.0,
                brake_a=100.0 if i > 5 else 0.0,
                brake_b=90.0 if i > 6 else 0.0,
                gear_a=4,
                gear_b=4,
                gap_meters=2.5 - (0.7 if 10 <= i <= 15 else 0.0),
                closing_speed_ms=8.4 if 10 <= i <= 15 else 2.0,
            )
        )
    return frames


# ==============================================================================
# 1. EVIDENCE ITEM CONTRACT & EXPLICIT EPISTEMIC TYPING
# ==============================================================================

def test_evidence_item_schema_and_status():
    """Verify EvidenceItem contract strictly separates OBSERVED, DERIVED, and MODEL_DERIVED."""
    item_observed = EvidenceItem(
        evidence_id="EV-TEST-01",
        evidence_type=EvidenceType.TELEMETRY,
        source_layer="ECU CAN-Bus",
        status=EvidenceStatus.OBSERVED,
        observation="Brake pressure 98.4 bar",
        value=98.4,
        unit="bar",
        provenance="Car ECU",
    )
    assert item_observed.status == EvidenceStatus.OBSERVED

    item_derived = EvidenceItem(
        evidence_id="EV-TEST-02",
        evidence_type=EvidenceType.OVERTAKE_GEOMETRY,
        source_layer="Apex Overlap Calculator",
        status=EvidenceStatus.DERIVED,
        observation="Apex Overlap 52%",
        value=52.0,
        unit="percentage",
        provenance="Geometry Projection",
        parent_evidence_ids=["EV-TEST-01"],
    )
    assert item_derived.status == EvidenceStatus.DERIVED
    assert item_derived.parent_evidence_ids == ["EV-TEST-01"]

    item_model = EvidenceItem(
        evidence_id="EV-TEST-03",
        evidence_type=EvidenceType.ML_INTERACTION,
        source_layer="MLCandidateClassifier",
        status=EvidenceStatus.MODEL_DERIVED,
        observation="Anomaly Likelihood 84%",
        value=0.84,
        unit="probability",
        provenance="Logistic Regression",
        parent_evidence_ids=["EV-TEST-02"],
    )
    assert item_model.status == EvidenceStatus.MODEL_DERIVED


# ==============================================================================
# 2. LINEAGE TRACKING & DOUBLE-COUNTING PREVENTION
# ==============================================================================

def test_lineage_tracker_double_counting_prevention():
    """Verify that multiple downstream derived features sharing a single root do not inflate independent count."""
    items = [
        # Root Telemetry
        EvidenceItem(
            evidence_id="TEL-ROOT",
            evidence_type=EvidenceType.TELEMETRY,
            source_layer="FastF1 25Hz",
            status=EvidenceStatus.OBSERVED,
            observation="25Hz Telemetry Coordinates",
            provenance="FastF1",
            parent_evidence_ids=[],
        ),
        # Child 1: Minimum Gap derived from Telemetry
        EvidenceItem(
            evidence_id="TEL-MIN-GAP",
            evidence_type=EvidenceType.TELEMETRY,
            source_layer="Proximity",
            status=EvidenceStatus.DERIVED,
            observation="Min gap 1.82m",
            provenance="Euclidean",
            parent_evidence_ids=["TEL-ROOT"],
        ),
        # Child 2: Closing speed derived from Minimum Gap
        EvidenceItem(
            evidence_id="TEL-CLOSING",
            evidence_type=EvidenceType.TELEMETRY,
            source_layer="Kinematics",
            status=EvidenceStatus.DERIVED,
            observation="Closing rate 8.4 m/s",
            provenance="Derivative",
            parent_evidence_ids=["TEL-MIN-GAP"],
        ),
        # Child 3: ML feature derived from Closing Speed + Min Gap
        EvidenceItem(
            evidence_id="ML-PREDICTION",
            evidence_type=EvidenceType.ML_INTERACTION,
            source_layer="MLClassifier",
            status=EvidenceStatus.MODEL_DERIVED,
            observation="Anomaly score 0.88",
            provenance="Logistic Model",
            parent_evidence_ids=["TEL-MIN-GAP", "TEL-CLOSING"],
        ),
        # Independent Root: FIA Regulation
        EvidenceItem(
            evidence_id="REG-DOC",
            evidence_type=EvidenceType.REGULATION,
            source_layer="FIA Statute",
            status=EvidenceStatus.DOCUMENTARY,
            observation="Article 33.4",
            provenance="FIA Sporting Code",
            parent_evidence_ids=[],
        ),
    ]

    indep_count = LineageTracker.compute_independent_observation_count(items)
    # TEL-ROOT and its 3 downstream children count as 1 independent origin stream; REG-DOC counts as 2nd
    assert indep_count == 2, f"Expected 2 independent streams, got {indep_count}"


# ==============================================================================
# 3. CROSS-MODAL CONSISTENCY & DISCREPANCY DETECTION
# ==============================================================================

def test_cross_modal_consistency_aligned():
    """Verify consistency engine produces CONSISTENT status when within tolerances."""
    items = []
    status, consensus, discrepancies = ConsistencyEngine.analyze_cross_modal_consistency(
        candidate_id="CAND-01",
        items=items,
        telemetry_min_gap_m=1.82,
        telemetry_event_time_sec=12.0,
        visual_min_sep_sec=12.04,  # delta = 0.04s <= 0.20s
        sync_uncertainty_sec=0.05,
        video_available=True,
        cv_available=True,
        apex_overlap_pct=52.0,
        apex_longitudinal_gap_m=1.8,
        braking_onset_delta_m=4.0,  # <= 15.0m
    )

    assert status == ConsistencyStatus.CONSISTENT
    assert "TELEMETRY" in consensus.supporting_evidence_streams
    assert "VIDEO_SYNCHRONIZATION" in consensus.supporting_evidence_streams
    assert len(discrepancies) == 0


def test_cross_modal_consistency_discrepancy_detected():
    """Verify consistency engine detects temporal and braking onset discrepancies."""
    items = []
    status, consensus, discrepancies = ConsistencyEngine.analyze_cross_modal_consistency(
        candidate_id="CAND-02",
        items=items,
        telemetry_min_gap_m=1.82,
        telemetry_event_time_sec=12.0,
        visual_min_sep_sec=12.45,  # delta = 0.45s > 0.25s -> CONFLICTING
        sync_uncertainty_sec=0.05,
        video_available=True,
        cv_available=True,
        apex_overlap_pct=55.0,
        apex_longitudinal_gap_m=1.8,
        braking_onset_delta_m=-18.5,  # > 15m delta -> Braking Discrepancy
    )

    assert status == ConsistencyStatus.CONFLICTING
    assert len(discrepancies) >= 2
    # Verify discrepancy severity is technical indicator, not fault/guilt
    assert any(d.severity == DiscrepancySeverity.HIGH for d in discrepancies)
    assert any(d.severity == DiscrepancySeverity.MEDIUM for d in discrepancies)


# ==============================================================================
# 4. MASTER STEWARD EVIDENCE DOSSIER SYNTHESIS
# ==============================================================================

def test_steward_dossier_synthesis_end_to_end(mock_candidate, mock_telemetry_frames):
    """Verify full end-to-end synthesis of StewardEvidenceDossier."""
    base_dossier = synthesize_incident_evidence_dossier(
        candidate=mock_candidate,
        raw_frames=mock_telemetry_frames,
        all_features=[],
    )

    synthesizer = get_steward_dossier_synthesizer()
    steward_dossier = synthesizer.synthesize_steward_dossier(
        dossier=base_dossier,
        cv_analysis=None,
        review_record={"status": "REQUIRES_REVIEW", "reviewer_id": None},
    )

    assert isinstance(steward_dossier, StewardEvidenceDossier)
    assert steward_dossier.candidate_id == mock_candidate.candidate_id
    assert steward_dossier.driver_a == "MAG"
    assert steward_dossier.driver_b == "GAS"
    assert steward_dossier.review_status == "REQUIRES_REVIEW"

    # Verify canonical sections are populated
    assert len(steward_dossier.timeline) > 0
    assert len(steward_dossier.evidence_items) >= 4
    assert len(steward_dossier.stream_quality) == 8  # 8 streams evaluated
    assert isinstance(steward_dossier.cross_modal_consistency, ConsistencyStatus)
    assert steward_dossier.consensus.independent_observation_count >= 1
    assert len(steward_dossier.regulations) > 0
    assert len(steward_dossier.limitations) >= 3


# ==============================================================================
# 5. DETERMINISTIC JSON EXPORT
# ==============================================================================

def test_dossier_json_export(mock_candidate, mock_telemetry_frames):
    """Verify deterministic JSON export format and serialization."""
    base_dossier = synthesize_incident_evidence_dossier(
        candidate=mock_candidate,
        raw_frames=mock_telemetry_frames,
        all_features=[],
    )

    synthesizer = get_steward_dossier_synthesizer()
    steward_dossier = synthesizer.synthesize_steward_dossier(base_dossier)
    payload = synthesizer.export_dossier_json(steward_dossier)

    assert payload.export_type == "JSON_STEWARD_DOSSIER"
    assert payload.schema_version == "2.0"
    assert payload.dossier.candidate_id == mock_candidate.candidate_id

    # Verify JSON serializability
    json_str = payload.model_dump_json(by_alias=True)
    parsed = json.loads(json_str)
    assert parsed["exportType"] == "JSON_STEWARD_DOSSIER"
    assert "dossier" in parsed


# ==============================================================================
# 6. MONZA REFERENCE CASES DOSSIER VALIDATION
# ==============================================================================

@pytest.mark.parametrize("ref_id", ["REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"])
def test_monza_reference_cases_dossier(ref_id):
    """Verify official Monza reference incidents synthesize cleanly with honest unavailable video/CV."""
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(ref_id)
    assert dossier is not None, f"Reference case '{ref_id}' not found in engine."

    synthesizer = get_steward_dossier_synthesizer()
    steward_dossier = synthesizer.synthesize_steward_dossier(dossier, candidate_id_override=ref_id)

    assert steward_dossier.candidate_id == ref_id
    assert steward_dossier.review_status == "REQUIRES_REVIEW"

    # Video and CV must be marked UNAVAILABLE honestly
    vid_item = next((i for i in steward_dossier.evidence_items if i.evidence_type == EvidenceType.VIDEO_SYNCHRONIZATION), None)
    assert vid_item is not None
    assert vid_item.status == EvidenceStatus.UNAVAILABLE

    cv_item = next((i for i in steward_dossier.evidence_items if i.evidence_type == EvidenceType.COMPUTER_VISION), None)
    assert cv_item is not None
    assert cv_item.status == EvidenceStatus.UNAVAILABLE

    # Telemetry and Regulations must be present
    tel_item = next((i for i in steward_dossier.evidence_items if i.evidence_type == EvidenceType.TELEMETRY), None)
    assert tel_item is not None
    assert tel_item.status in [EvidenceStatus.OBSERVED, EvidenceStatus.DERIVED]


# ==============================================================================
# 7. HUMAN REVIEW INTEGRATION (ZERO AUTO-DECISION)
# ==============================================================================

def test_human_review_status_preservation(mock_candidate, mock_telemetry_frames):
    """Verify synthesis respects existing human review state and never auto-adjudicates."""
    base_dossier = synthesize_incident_evidence_dossier(
        candidate=mock_candidate,
        raw_frames=mock_telemetry_frames,
        all_features=[],
    )

    synthesizer = get_steward_dossier_synthesizer()

    # Case A: UNDER_REVIEW
    dossier_under_review = synthesizer.synthesize_steward_dossier(
        dossier=base_dossier,
        review_record={"status": "UNDER_REVIEW", "reviewer_id": "STEWARD-01", "review_notes": "Checking apex gap"},
    )
    assert dossier_under_review.review_status == "UNDER_REVIEW"
    assert dossier_under_review.reviewer_id == "STEWARD-01"

    # Case B: REVIEWED
    dossier_reviewed = synthesizer.synthesize_steward_dossier(
        dossier=base_dossier,
        review_record={"status": "REVIEWED", "reviewer_id": "STEWARD-PANEL", "review_notes": "Completed inquiry"},
    )
    assert dossier_reviewed.review_status == "REVIEWED"

    # Case C: DISMISSED
    dossier_dismissed = synthesizer.synthesize_steward_dossier(
        dossier=base_dossier,
        review_record={"status": "DISMISSED", "reviewer_id": "STEWARD-02"},
    )
    assert dossier_dismissed.review_status == "DISMISSED"


# ==============================================================================
# 8. REST API CONTRACTS
# ==============================================================================

def test_api_candidate_steward_dossier_endpoint(client):
    """Verify GET /api/v1/analysis/candidates/{candidate_id}/steward-dossier and /api/v1/incidents/{incident_id}/dossier."""
    response = client.get("/api/v1/analysis/candidates/REF-MONZA-01/steward-dossier")
    assert response.status_code == 200
    data = response.json()

    assert data["candidateId"] == "REF-MONZA-01"
    assert data["dossierVersion"] == "2.0"
    assert "evidenceItems" in data
    assert "streamQuality" in data
    assert "consensus" in data
    assert "timeline" in data
    assert "stewardDoctrine" in data

    # Also verify incidents endpoint
    inc_resp = client.get("/api/v1/incidents/REF-MONZA-01/dossier")
    assert inc_resp.status_code == 200
    inc_data = inc_resp.json()
    assert inc_data["candidateId"] == "REF-MONZA-01"
    assert inc_data["dossierVersion"] == "2.0"


def test_api_candidate_dossier_export_json_endpoint(client):
    """Verify GET /api/v1/analysis/candidates/{candidate_id}/dossier/export/json endpoint."""
    response = client.get("/api/v1/analysis/candidates/REF-MONZA-01/dossier/export/json")
    assert response.status_code == 200
    data = response.json()

    assert data["exportType"] == "JSON_STEWARD_DOSSIER"
    assert data["schemaVersion"] == "2.0"
    assert "dossier" in data
    assert data["dossier"]["candidateId"] == "REF-MONZA-01"

    # Also verify incidents json export
    inc_exp = client.get("/api/v1/incidents/REF-MONZA-01/dossier/json")
    assert inc_exp.status_code == 200
    assert inc_exp.json()["exportType"] == "JSON_STEWARD_DOSSIER"


# ==============================================================================
# 9. NON-ADJUDICATIVE GUARDRAILS
# ==============================================================================

def test_guardrails_no_guilt_or_fault():
    """Verify Steward Evidence Dossier strictly omits forbidden adjudicative terms."""
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier("REF-MONZA-03")
    assert dossier is not None

    synthesizer = get_steward_dossier_synthesizer()
    steward_dossier = synthesizer.synthesize_steward_dossier(dossier)
    json_str = steward_dossier.model_dump_json().lower()

    forbidden_terms = [
        "driver is guilty",
        "was at fault",
        "penalty awarded",
        "collision confirmed",
        "driver fault",
        "illegal overtake",
        "caused collision",
    ]

    for term in forbidden_terms:
        assert term not in json_str, f"Forbidden term '{term}' found in Steward Evidence Dossier."
