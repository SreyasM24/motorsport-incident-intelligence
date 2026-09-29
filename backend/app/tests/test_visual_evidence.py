"""Unit and integration test suite for Bounded Visual Evidence & Multi-Modal Alignment (Prompt 13).

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS:
    1. Zero Autonomous Guilt or Fault Determination: Visual features (IoU, centroid proximity)
       must NEVER assert fault, blame, penalty, or contact guilt.
    2. Zero Copyright Infringement & Zero Hallucination: Real Grand Prix sessions without licensed
       broadcast footage (e.g. Monza 2024 reference cases) must honestly default to UNAVAILABLE.
    3. Test Fixture Isolation: Synthetic tests must use explicitly marked TEST_FIXTURE metadata.
    4. Orthogonal Decision Support: Human steward review remains the sole decision authority.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.evidence.video_evidence import (
    AnchorEventType,
    CalibrationPoint,
    SyncMethod,
    VideoProvenanceRecord,
    VideoSourceMetadata,
    VideoSourceType,
    VideoSyncStatus,
    compute_calibration_transform,
)
from app.evidence.visual.models import (
    AlignmentStatus,
    ApproachTrend,
    CrossModalAlignment,
    DriverAssociationStatus,
    VisibilityState,
    VisualEvidenceQualityRating,
    VisualEvidenceSummary,
    VisualFeatureEvidence,
    VisualKeyframe,
    VisualObservationStatus,
    VisualROI,
    VisualTrackObservation,
)
from app.evidence.visual.extractor import (
    VisualKeyframeExtractor,
    compute_cross_modal_alignment,
)
from app.evidence.visual.service import (
    VisualEvidenceService,
    get_visual_evidence_service,
)
from app.evidence.candidate import (
    CandidateDossier,
    CandidateEventType,
    CandidateStatus,
    DataQualityFlags,
)
from app.evidence.dossier import (
    IncidentEvidenceDossier,
    convert_dossier_to_frontend_incident,
    synthesize_incident_evidence_dossier,
)
from app.schemas.telemetry import TelemetryPointSchema


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def synthetic_fixture_source():
    """Create a calibrated test fixture video source for automated tests."""
    pts = [
        CalibrationPoint(
            point_id="PT-TEST-1",
            name="Session Sync Point",
            video_time_sec=10.0,
            session_time_sec=0.0,
            anchor_type=AnchorEventType.START_FINISH_CROSSING,
        )
    ]
    transform = compute_calibration_transform(
        pts, method=SyncMethod.DIRECT_TIMESTAMP, nominal_frame_rate=50.0
    )
    return VideoSourceMetadata(
        video_id="FIXTURE-CAM-WF",
        source_type=VideoSourceType.BROADCAST.value,
        source_url="/fixtures/test_world_feed.mp4",
        source_reference="Synthetic Test Fixture - World Feed",
        session_id="test-session-fixture-2024",
        camera_label="Test Broadcast World Feed",
        duration_sec=3600.0,
        sync_status=VideoSyncStatus.VIDEO_SYNCHRONIZED,
        frame_rate=50.0,
        resolution="1920x1080",
        timezone="UTC",
        transform=transform,
        calibration_points=pts,
        availability_status="AVAILABLE",
        provenance=VideoProvenanceRecord(
            source="Synthetic Test Engine",
            source_reference="TEST_FIXTURE_RECORD",
            acquisition_method="TEST_FIXTURE",
            session="test-session-fixture-2024",
            camera="Test World Feed",
            timestamp_basis="SMPTE_LTC",
            availability="STREAM_AVAILABLE",
            metadata_quality="HIGH",
        ),
    )


# ==============================================================================
# 1. DATA MODEL & GEOMETRIC MATH TESTS
# ==============================================================================

def test_visual_observation_status_values():
    """Verify strictly defined status enum values."""
    assert VisualObservationStatus.OBSERVED.value == "OBSERVED"
    assert VisualObservationStatus.DERIVED.value == "DERIVED"
    assert VisualObservationStatus.UNAVAILABLE.value == "UNAVAILABLE"


def test_visual_roi_math_and_iou():
    """Verify deterministic 2D IoU calculation in normalized image coordinates."""
    # Box 1: [0.1, 0.1, 0.5, 0.5] -> width=0.4, height=0.4, area=0.16
    roi1 = VisualROI(
        roi_id="ROI-1",
        camera_id="CAM-1",
        x_min=0.1,
        y_min=0.1,
        x_max=0.5,
        y_max=0.5,
    )
    assert roi1.width == 0.4
    assert roi1.height == 0.4
    assert round(roi1.area, 4) == 0.16
    assert roi1.centroid == (0.3, 0.3)

    # Identical box -> IoU = 1.0
    assert roi1.compute_iou(roi1) == 1.0

    # Completely disjoint box -> IoU = 0.0
    roi_disjoint = VisualROI(
        roi_id="ROI-DISJOINT",
        camera_id="CAM-1",
        x_min=0.6,
        y_min=0.6,
        x_max=0.9,
        y_max=0.9,
    )
    assert roi1.compute_iou(roi_disjoint) == 0.0

    # Overlapping box: [0.3, 0.3, 0.7, 0.7] -> intersection [0.3, 0.3, 0.5, 0.5] (0.2 x 0.2 = 0.04)
    # Area roi1 = 0.16, Area roi2 = 0.16, Union = 0.16 + 0.16 - 0.04 = 0.28
    # IoU = 0.04 / 0.28 = 1/7 ~= 0.1429
    roi_overlap = VisualROI(
        roi_id="ROI-OVERLAP",
        camera_id="CAM-1",
        x_min=0.3,
        y_min=0.3,
        x_max=0.7,
        y_max=0.7,
    )
    iou = roi1.compute_iou(roi_overlap)
    assert abs(iou - (0.04 / 0.28)) < 1e-3


def test_visual_track_observation_contract():
    """Verify contract for single vehicle track observation."""
    roi = VisualROI(
        roi_id="ROI-20",
        camera_id="CAM-1",
        x_min=0.4,
        y_min=0.4,
        x_max=0.6,
        y_max=0.6,
    )
    obs = VisualTrackObservation(
        track_id="TRK-20",
        driver_number="20",
        driver_code="MAG",
        association_status=DriverAssociationStatus.CONFIRMED,
        centroid_x=0.5,
        centroid_y=0.5,
        bbox=roi,
        visibility=VisibilityState.IN_FRAME,
        detection_confidence=0.95,
        track_persistence_frames=12,
    )
    assert obs.track_id == "TRK-20"
    assert obs.driver_code == "MAG"
    assert obs.association_status == DriverAssociationStatus.CONFIRMED
    assert obs.visibility == VisibilityState.IN_FRAME


# ==============================================================================
# 2. KEYFRAME EXTRACTOR TESTS
# ==============================================================================

def test_keyframe_extractor_synthetic_fixture(synthetic_fixture_source):
    """Verify synthetic test fixture extracts 4 synchronized keyframes with bounded features."""
    extractor = VisualKeyframeExtractor()
    keyframes = extractor.extract_keyframes(
        source=synthetic_fixture_source,
        event_peak_sec=100.0,
        driver_a="20",
        driver_b="27",
    )
    assert len(keyframes) == 4
    rel_times = [kf.event_relative_time_sec for kf in keyframes]
    assert rel_times == [-1.5, -0.5, 0.0, 1.0]

    # Verify peak proximity frame (relative time 0.0)
    apex_kf = next(k for k in keyframes if k.event_relative_time_sec == 0.0)
    assert len(apex_kf.observations) == 2
    assert apex_kf.features is not None
    assert apex_kf.features.bbox_overlap_iou > 0.0
    assert apex_kf.features.measurement_basis == "BOUNDED_2D_PROJECTION"


def test_keyframe_extractor_unavailable_source():
    """Verify unlinked or unavailable sources return empty keyframes honestly without fabricating data."""
    extractor = VisualKeyframeExtractor()
    unavail_source = VideoSourceMetadata(
        video_id="UNAVAIL-CAM",
        source_type=VideoSourceType.BROADCAST.value,
        source_reference="Unlinked Source",
        session_id="f1-2024-ita-race",
        camera_label="Broadcast",
        sync_status=VideoSyncStatus.VIDEO_UNAVAILABLE,
        availability_status="UNAVAILABLE",
    )
    keyframes = extractor.extract_keyframes(
        source=unavail_source,
        event_peak_sec=100.0,
    )
    assert keyframes == []


# ==============================================================================
# 3. CROSS-MODAL ALIGNMENT TESTS
# ==============================================================================

def test_cross_modal_alignment_aligned(synthetic_fixture_source):
    """Verify ALIGNED status when visual minimum separation matches telemetry peak."""
    extractor = VisualKeyframeExtractor()
    keyframes = extractor.extract_keyframes(
        source=synthetic_fixture_source,
        event_peak_sec=100.0,
    )
    alignment = compute_cross_modal_alignment(
        telemetry_peak_sec=100.0,
        keyframes=keyframes,
        sync_uncertainty_sec=0.04,
        tolerance_sec=0.20,
    )
    assert alignment.alignment_status == AlignmentStatus.ALIGNED
    assert alignment.delta_seconds == 0.0
    assert "aligns with telemetry peak" in alignment.description


def test_cross_modal_alignment_partially_aligned(synthetic_fixture_source):
    """Verify PARTIALLY_ALIGNED when delta falls between tolerance and combined uncertainty."""
    extractor = VisualKeyframeExtractor()
    keyframes = extractor.extract_keyframes(
        source=synthetic_fixture_source,
        event_peak_sec=100.0,
    )
    # Telemetry peak shifted by 0.25s (tolerance is 0.20s, uncertainty is 0.10s)
    alignment = compute_cross_modal_alignment(
        telemetry_peak_sec=100.25,
        keyframes=keyframes,
        sync_uncertainty_sec=0.10,
        tolerance_sec=0.20,
    )
    assert alignment.alignment_status == AlignmentStatus.PARTIALLY_ALIGNED
    assert "falls within combined tolerance and synchronization uncertainty" in alignment.description


def test_cross_modal_alignment_misaligned(synthetic_fixture_source):
    """Verify MISALIGNED when discrepancy exceeds tolerance and uncertainty bounds."""
    extractor = VisualKeyframeExtractor()
    keyframes = extractor.extract_keyframes(
        source=synthetic_fixture_source,
        event_peak_sec=100.0,
    )
    alignment = compute_cross_modal_alignment(
        telemetry_peak_sec=105.0,  # 5 seconds off
        keyframes=keyframes,
        sync_uncertainty_sec=0.04,
        tolerance_sec=0.20,
    )
    assert alignment.alignment_status == AlignmentStatus.MISALIGNED
    assert "Significant temporal discrepancy detected" in alignment.description


def test_cross_modal_alignment_insufficient_data():
    """Verify INSUFFICIENT_DATA status when no keyframes are provided."""
    alignment = compute_cross_modal_alignment(
        telemetry_peak_sec=100.0,
        keyframes=[],
    )
    assert alignment.alignment_status == AlignmentStatus.INSUFFICIENT_DATA
    assert alignment.delta_seconds is None


# ==============================================================================
# 4. MONZA 2024 HONEST UNAVAILABLE AUDIT
# ==============================================================================

@pytest.mark.parametrize("ref_id", ["REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"])
def test_monza_reference_cases_honest_unavailable(ref_id):
    """Verify that all Monza 2024 reference cases honestly return UNAVAILABLE visual evidence."""
    service = get_visual_evidence_service()
    evidence = service.build_visual_evidence_for_candidate(
        candidate_id=ref_id,
        session_id="f1-2024-italian grand prix-race",
        event_start_str="2024-09-01 13:04:00.000",
        event_peak_str="2024-09-01 13:04:05.000",
        event_end_str="2024-09-01 13:04:10.000",
    )
    assert evidence.status == VisualObservationStatus.UNAVAILABLE
    assert len(evidence.keyframes) == 0
    assert len(evidence.track_observations) == 0
    assert "commercial copyright" in evidence.statement
    assert "Missing visual evidence is treated as an honest unobserved state" in evidence.statement
    assert evidence.cross_modal_alignment.alignment_status == AlignmentStatus.INSUFFICIENT_DATA


# ==============================================================================
# 5. DOSSIER & FRONTEND INCIDENT INTEGRATION TESTS
# ==============================================================================

def test_dossier_synthesis_includes_visual_evidence():
    """Verify that synthesizing an IncidentEvidenceDossier includes visual evidence."""
    cand = CandidateDossier(
        candidate_id="TEST-CAND-VIS-01",
        session_id="f1-2024-monza-race",
        event_type=CandidateEventType.RAPID_PROXIMITY_EVENT,
        status=CandidateStatus.PENDING_REVIEW,
        driver_a="20",
        driver_b="27",
        lap_number_a=19,
        lap_number_b=19,
        event_start="2024-09-01 13:30:00.000",
        event_peak="2024-09-01 13:30:05.000",
        event_end="2024-09-01 13:30:10.000",
        duration_seconds=10.0,
        minimum_gap_meters=2.1,
        peak_closing_speed_ms=4.5,
        speed_delta_at_peak=0.0,
        speed_a_at_peak=200.0,
        speed_b_at_peak=200.0,
        braking_change={"decel_delta_g": 0.3},
        evidence_strength=85,
        summary="Turn 4 contested corner entry",
        detection_method="TELEMETRY_KINEMATICS",
        data_quality_flags=DataQualityFlags(),
    )
    dummy_points = [
        TelemetryPointSchema(
            timestamp=f"2024-09-01 13:30:0{i}.000",
            time_offset=float(i) * 0.2,
            driver_a="20",
            driver_b="27",
            gap_meters=3.0 - (i * 0.2),
            closing_speed_ms=2.0,
            speed_a=280.0 - (i * 20),
            speed_b=282.0 - (i * 20),
            throttle_a=0.0,
            throttle_b=0.0,
            brake_a=1.0,
            brake_b=1.0,
            gear_a=4,
            gear_b=4,
            lap_a=19,
            lap_b=19,
        )
        for i in range(5)
    ]
    dossier = synthesize_incident_evidence_dossier(
        candidate=cand,
        raw_frames=dummy_points,
        all_features=[],
    )
    assert hasattr(dossier, "visual_evidence")
    assert dossier.visual_evidence is not None
    assert hasattr(dossier.video_evidence, "visual_evidence")


def test_convert_dossier_to_frontend_incident_with_visual_evidence(synthetic_fixture_source):
    """Verify that convert_dossier_to_frontend_incident attaches visual evidence assessment."""
    service = get_visual_evidence_service()
    vis_summary = service.build_visual_evidence_for_candidate(
        candidate_id="TEST-CAND-VIS-02",
        session_id="test-session-fixture-2024",
        event_start_str="2024-09-01 13:30:00.000",
        event_peak_str="2024-09-01 13:30:05.000",
        event_end_str="2024-09-01 13:30:10.000",
        driver_a="20",
        driver_b="27",
        selected_source=synthetic_fixture_source,
    )
    assert vis_summary.status == VisualObservationStatus.OBSERVED

    cand = CandidateDossier(
        candidate_id="TEST-CAND-VIS-02",
        session_id="test-session-fixture-2024",
        event_type=CandidateEventType.RAPID_PROXIMITY_EVENT,
        status=CandidateStatus.PENDING_REVIEW,
        driver_a="20",
        driver_b="27",
        lap_number_a=1,
        lap_number_b=1,
        event_start="2024-09-01 13:30:00.000",
        event_peak="2024-09-01 13:30:05.000",
        event_end="2024-09-01 13:30:10.000",
        duration_seconds=10.0,
        minimum_gap_meters=1.8,
        peak_closing_speed_ms=5.0,
        speed_delta_at_peak=0.0,
        speed_a_at_peak=200.0,
        speed_b_at_peak=200.0,
        braking_change={"decel_delta_g": 0.4},
        evidence_strength=90,
        summary="Test incident with visual observations",
        detection_method="TELEMETRY_KINEMATICS",
        data_quality_flags=DataQualityFlags(),
    )
    dummy_points = [
        TelemetryPointSchema(
            timestamp=f"2024-09-01 13:30:0{i}.000",
            time_offset=float(i) * 0.2,
            driver_a="20",
            driver_b="27",
            gap_meters=2.5 - (i * 0.1),
            closing_speed_ms=2.0,
            speed_a=250.0,
            speed_b=250.0,
            throttle_a=0.0,
            throttle_b=0.0,
            brake_a=1.0,
            brake_b=1.0,
            gear_a=3,
            gear_b=3,
            lap_a=1,
            lap_b=1,
        )
        for i in range(5)
    ]
    dossier = synthesize_incident_evidence_dossier(
        candidate=cand,
        raw_frames=dummy_points,
        all_features=[],
        video_source=synthetic_fixture_source,
    )
    dossier.visual_evidence = vis_summary

    frontend_inc = convert_dossier_to_frontend_incident(dossier)
    assert frontend_inc.visual_evidence is not None

    # Check that a VISUAL evidence assessment item was added
    vis_items = [ev for ev in frontend_inc.evidence_assessment if ev.category == "VISUAL"]
    assert len(vis_items) >= 1
    assert "Cross-Modal Status: ALIGNED" in vis_items[0].observed_value


# ==============================================================================
# 6. REST API ENDPOINT TESTS
# ==============================================================================

def test_api_candidate_visual_evidence_monza(test_client):
    """Verify GET /api/v1/analysis/candidates/{candidate_id}/video/visual-evidence for Monza case."""
    resp = test_client.get("/api/v1/analysis/candidates/REF-MONZA-01/video/visual-evidence")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "UNAVAILABLE"
    assert "commercial copyright" in data["statement"]
    assert data["keyframes"] == []
    assert data["crossModalAlignment"]["alignmentStatus"] == "INSUFFICIENT_DATA"


def test_api_candidate_visual_evidence_not_found(test_client):
    """Verify 404 response when candidate does not exist."""
    resp = test_client.get("/api/v1/analysis/candidates/NON_EXISTENT_CANDIDATE/video/visual-evidence")
    assert resp.status_code == 404


# ==============================================================================
# 7. GUARDRAIL VERIFICATION: NO AUTONOMOUS GUILT OR PENALTIES
# ==============================================================================

def test_bounded_guardrails_no_guilt_or_fault(synthetic_fixture_source):
    """Verify that visual evidence outputs contain zero fault, blame, guilt, or penalty assertions."""
    service = get_visual_evidence_service()
    vis_summary = service.build_visual_evidence_for_candidate(
        candidate_id="TEST-FIXTURE-GUARDRAILS",
        session_id="test-session-fixture-2024",
        event_start_str="2024-09-01 13:30:00.000",
        event_peak_str="2024-09-01 13:30:05.000",
        event_end_str="2024-09-01 13:30:10.000",
        driver_a="20",
        driver_b="27",
        selected_source=synthetic_fixture_source,
    )
    all_text = " ".join([
        vis_summary.statement,
        " ".join(vis_summary.limitations),
        vis_summary.cross_modal_alignment.description if vis_summary.cross_modal_alignment else "",
    ]).lower()

    prohibited_terms = [
        "guilty",
        "at fault",
        "penalty applied",
        "penalty recommended",
        "infringement confirmed",
        "guilt",
        "illegal move",
        "liable",
    ]
    for term in prohibited_terms:
        assert term not in all_text, f"Prohibited adjudicative term '{term}' found in visual evidence output."
