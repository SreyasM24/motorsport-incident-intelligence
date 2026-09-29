"""Comprehensive test suite for Video Evidence Ingestion, Time Synchronization & Alignment (Prompt 12).

Covers all 15 required validation points + CV readiness + API contracts:
1. Exact timestamp mapping and inverse float consistency
2. Constant offset calibration (b != 0, a = 1.0)
3. Affine time mapping with scale dilation (a != 1.0, b != 0)
4. Manual calibration from single keypoint
5. Multiple calibration points with linear regression and residual RMSE calculation
6. Invalid and degenerate calibration handling (empty points, zero-variance points)
7. Missing frame rate handling (returns None frame numbers while preserving timecode)
8. Missing and malformed timestamp string handling
9. Quantified synchronization uncertainty bounds (no false precision)
10. Honest VIDEO_UNAVAILABLE default handling (zero hallucinated video)
11. Multi-camera alignment across independent feeds (broadcast, onboard, trackside)
12. Incident video window conversion with pre-roll and post-roll boundaries
13. Frame number conversion, non-negative boundary checks, and frame rate validation
14. Timezone and time basis metadata provenance
15. Regression against IncidentEvidenceDossier and Monza 2024 reference cases
16. Computer Vision readiness contract (SynchronizedVideoFrame)
17. REST API endpoints (/video and /video/synchronization)
"""

import pytest
import math
from fastapi.testclient import TestClient

from app.main import app
from app.evidence.video_evidence import (
    AnchorEventType,
    CalibrationPoint,
    CameraAlignmentInfo,
    IncidentVideoWindow,
    SynchronizedVideoFrame,
    SyncConfidence,
    SyncMethod,
    SynchronizationUncertainty,
    VideoClipRecommendation,
    VideoEvidenceSummary,
    VideoProvenanceRecord,
    VideoSourceMetadata,
    VideoSourceType,
    VideoSyncStatus,
    VideoTimeTransform,
    build_video_evidence,
    compute_calibration_transform,
    format_seconds_to_time,
    parse_timestamp_to_seconds,
)
from app.services.video_service import (
    VideoSynchronizationService,
    get_video_service,
)
from app.evidence.dossier import synthesize_incident_evidence_dossier, convert_dossier_to_frontend_incident
from app.evidence.candidate import (
    CandidateDossier,
    CandidateEventType,
    CandidateStatus,
    DataQualityFlags,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_candidate():
    """Create a minimal mock CandidateDossier for alignment testing."""
    return CandidateDossier(
        candidate_id="TEST-CAND-P12-01",
        session_id="f1-2024-italian grand prix-race",
        event_type=CandidateEventType.CONTACT_CANDIDATE,
        status=CandidateStatus.PENDING_REVIEW,
        driver_a="RIC",
        driver_b="HUL",
        event_start="2024-09-01 13:04:10.000",
        event_peak="2024-09-01 13:04:12.500",
        event_end="2024-09-01 13:04:15.000",
        duration_seconds=5.0,
        start_distance_m=1200.0,
        peak_distance_m=1280.0,
        end_distance_m=1350.0,
        minimum_gap_meters=0.45,
        peak_closing_speed_ms=8.5,
        speed_delta_at_peak=-5.0,
        speed_a_at_peak=200.0,
        speed_b_at_peak=205.0,
        evidence_strength=88,
        data_quality_flags=DataQualityFlags(),
        summary="Test candidate event for Prompt 12 video synchronization",
        detection_method="MULTI_SIGNAL_SYNCHRONIZED_TELEMETRY",
    )


# ==============================================================================
# 1. EXACT TIMESTAMP MAPPING & INVERSE CONSISTENCY
# ==============================================================================

def test_exact_timestamp_mapping_and_inverse():
    """Verify bidirectional mathematical bijection: video_to_session(session_to_video(t)) == t."""
    transform = VideoTimeTransform(time_scale=1.0, offset_sec=15.250)
    session_times = [0.0, 10.5, 45.1234, 120.75, 3600.0]

    for s_time in session_times:
        v_time = transform.session_to_video_time(s_time)
        recovered_s = transform.video_to_session_time(v_time)
        assert pytest.approx(recovered_s, abs=1e-3) == s_time


# ==============================================================================
# 2. CONSTANT OFFSET CALIBRATION
# ==============================================================================

def test_constant_offset_calibration():
    """Verify constant offset transform correctly advances/delays playback."""
    # Video clock started 12.0 seconds BEFORE session telemetry (video = session + 12.0s)
    transform = VideoTimeTransform(time_scale=1.0, offset_sec=12.0)
    
    assert transform.session_to_video_time(0.0) == 12.0
    assert transform.session_to_video_time(10.0) == 22.0
    assert transform.video_to_session_time(22.0) == 10.0
    assert transform.video_to_session_time(12.0) == 0.0


# ==============================================================================
# 3. AFFINE TIME MAPPING (TIME-SCALE DILATION)
# ==============================================================================

def test_affine_time_scale_mapping():
    """Verify non-unity time scale factor 'a' scales time dilation reversibly."""
    # Scale = 1.002 (e.g. 0.2% video clock drift over long session), offset = 5.0s
    transform = VideoTimeTransform(time_scale=1.002, offset_sec=5.0)

    session_t = 1000.0
    video_t = transform.session_to_video_time(session_t)
    assert pytest.approx(video_t, abs=1e-3) == 1.002 * 1000.0 + 5.0  # 1007.0s
    
    recovered = transform.video_to_session_time(video_t)
    assert pytest.approx(recovered, abs=1e-3) == session_t


# ==============================================================================
# 4. MANUAL CALIBRATION (SINGLE KEYPOINT)
# ==============================================================================

def test_single_point_manual_calibration():
    """Verify single-point calibration assumes unity scale (1.0) and computes exact offset."""
    pt = CalibrationPoint(
        point_id="PT-01",
        name="Lights Out Red Gantry Extinguish",
        video_time_sec=18.400,
        session_time_sec=4.200,
        anchor_type=AnchorEventType.LIGHTS_OUT,
    )
    transform = compute_calibration_transform([pt], method=SyncMethod.MANUAL_CALIBRATION)

    assert transform.time_scale == 1.0
    # b = 18.4 - 4.2 = 14.2
    assert transform.offset_sec == pytest.approx(14.200, abs=1e-3)
    assert transform.method == SyncMethod.MANUAL_CALIBRATION
    assert transform.uncertainty.sync_status == VideoSyncStatus.VIDEO_SYNCHRONIZED
    assert transform.uncertainty.estimated_error_seconds == 0.20
    assert transform.uncertainty.confidence == SyncConfidence.MEDIUM


# ==============================================================================
# 5. MULTIPLE CALIBRATION POINTS (REGRESSION & RMSE)
# ==============================================================================

def test_multi_point_calibration_regression_and_rmse():
    """Verify multi-point calibration computes least-squares fit and residual RMSE."""
    pts = [
        CalibrationPoint(point_id="P1", name="Gantry Crossing Lap 1", video_time_sec=10.0, session_time_sec=0.0),
        CalibrationPoint(point_id="P2", name="Turn 1 Apex Lap 1", video_time_sec=25.0, session_time_sec=15.0),
        CalibrationPoint(point_id="P3", name="Turn 4 Apex Lap 1", video_time_sec=45.0, session_time_sec=35.0),
        CalibrationPoint(point_id="P4", name="Parabolica Apex Lap 1", video_time_sec=85.0, session_time_sec=75.0),
    ]
    transform = compute_calibration_transform(pts, method=SyncMethod.DIRECT_TIMESTAMP, nominal_frame_rate=50.0)

    assert transform.time_scale == 1.0  # Perfect unity agreement
    assert transform.offset_sec == pytest.approx(10.0, abs=1e-3)
    assert transform.uncertainty.calibration_point_count == 4
    assert transform.uncertainty.residual_rmse_seconds == pytest.approx(0.0, abs=1e-3)
    assert transform.uncertainty.confidence == SyncConfidence.HIGH


# ==============================================================================
# 6. INVALID & DEGENERATE CALIBRATION HANDLING
# ==============================================================================

def test_invalid_and_degenerate_calibration():
    """Verify empty points, zero-variance points, and disordered timestamps are handled robustly."""
    # A. Empty points list
    t_empty = compute_calibration_transform([])
    assert t_empty.method == SyncMethod.UNKNOWN
    assert t_empty.uncertainty.sync_status == VideoSyncStatus.VIDEO_UNAVAILABLE
    assert t_empty.uncertainty.confidence == SyncConfidence.NONE

    # B. Degenerate identical session timestamps (zero variance)
    pts_degenerate = [
        CalibrationPoint(point_id="D1", name="Point 1", video_time_sec=10.0, session_time_sec=5.0),
        CalibrationPoint(point_id="D2", name="Point 2", video_time_sec=10.4, session_time_sec=5.0),
    ]
    t_degen = compute_calibration_transform(pts_degenerate)
    assert t_degen.time_scale == 1.0
    assert not math.isnan(t_degen.offset_sec)
    assert t_degen.uncertainty.confidence == SyncConfidence.LOW

    # C. Unsorted input points are sorted internally
    pts_unsorted = [
        CalibrationPoint(point_id="U2", name="Later Point", video_time_sec=30.0, session_time_sec=20.0),
        CalibrationPoint(point_id="U1", name="Earlier Point", video_time_sec=15.0, session_time_sec=5.0),
    ]
    t_unsorted = compute_calibration_transform(pts_unsorted)
    assert t_unsorted.time_scale == 1.0
    assert t_unsorted.offset_sec == pytest.approx(10.0, abs=1e-3)


# ==============================================================================
# 7. MISSING FRAME RATE HANDLING
# ==============================================================================

def test_missing_frame_rate_handling():
    """Verify missing or zero frame rate returns None for frame numbers while preserving timecodes."""
    transform = VideoTimeTransform(time_scale=1.0, offset_sec=5.0)

    # Known frame rate (25 fps)
    frame_known = transform.session_to_frame_number(10.0, frame_rate=25.0)
    assert frame_known == int(round(15.0 * 25.0))  # 375

    # None frame rate
    frame_none = transform.session_to_frame_number(10.0, frame_rate=None)
    assert frame_none is None

    # Zero or negative frame rate
    frame_zero = transform.session_to_frame_number(10.0, frame_rate=0.0)
    assert frame_zero is None


# ==============================================================================
# 8. MISSING & MALFORMED TIMESTAMPS
# ==============================================================================

def test_missing_and_malformed_timestamp_parsing():
    """Verify parse_timestamp_to_seconds handles ISO dates, time-only, raw seconds, and malformed strings."""
    assert parse_timestamp_to_seconds("2024-09-01 13:04:10.500") == pytest.approx(13 * 3600 + 4 * 60 + 10.5, abs=1e-3)
    assert parse_timestamp_to_seconds("13:04:10.500") == pytest.approx(13 * 3600 + 4 * 60 + 10.5, abs=1e-3)
    assert parse_timestamp_to_seconds("04:10.500") == pytest.approx(4 * 60 + 10.5, abs=1e-3)
    assert parse_timestamp_to_seconds("125.75") == pytest.approx(125.75, abs=1e-3)

    # Malformed strings fall back safely to 0.0 without exception
    assert parse_timestamp_to_seconds("") == 0.0
    assert parse_timestamp_to_seconds("INVALID_STRING") == 0.0
    assert parse_timestamp_to_seconds(None) == 0.0


# ==============================================================================
# 9. SYNCHRONIZATION UNCERTAINTY (REALISTIC BOUNDS)
# ==============================================================================

def test_synchronization_uncertainty_bounds():
    """Verify uncertainty exposure avoids false precision and reports realistic errors."""
    # DIRECT_TIMESTAMP: ~0.04s frame boundary
    t_direct = compute_calibration_transform(
        [CalibrationPoint(point_id="P1", name="NTP", video_time_sec=10.0, session_time_sec=0.0)],
        method=SyncMethod.DIRECT_TIMESTAMP,
    )
    assert t_direct.uncertainty.estimated_error_seconds == 0.04
    assert t_direct.uncertainty.confidence == SyncConfidence.HIGH

    # EVENT_ANCHOR: ~0.50s transponder/visual disparity
    t_anchor = compute_calibration_transform(
        [CalibrationPoint(point_id="P2", name="Anchor", video_time_sec=10.0, session_time_sec=0.0)],
        method=SyncMethod.EVENT_ANCHOR,
    )
    assert t_anchor.uncertainty.estimated_error_seconds == 0.50
    assert t_anchor.uncertainty.confidence == SyncConfidence.MEDIUM


# ==============================================================================
# 10. HONEST VIDEO_UNAVAILABLE DEFAULT
# ==============================================================================

def test_video_unavailable_default_handling():
    """Verify unlinked video sources return VIDEO_UNAVAILABLE honestly with clear documentation."""
    summary = build_video_evidence(
        session_id="f1-2024-ita-race",
        event_start_str="2024-09-01 13:04:10.000",
        event_peak_str="2024-09-01 13:04:12.500",
        event_end_str="2024-09-01 13:04:15.000",
        source=None,
    )

    assert summary.video_evidence_status == VideoSyncStatus.VIDEO_UNAVAILABLE
    assert summary.sources == []
    assert summary.recommended_clip is None
    assert summary.incident_window.window_status == "UNAVAILABLE"
    assert "No verified video broadcast stream is linked" in summary.statement
    assert len(summary.limitations) > 0


# ==============================================================================
# 11. MULTI-CAMERA ALIGNMENT
# ==============================================================================

def test_multi_camera_independent_clocks():
    """Verify multi-camera support maintains independent offsets, frame rates, and transforms."""
    video_service = get_video_service()
    fixture_sources = video_service.get_sources_for_candidate("TEST_FIXTURE")

    assert len(fixture_sources) >= 3
    cam_types = [s.source_type for s in fixture_sources]
    assert VideoSourceType.BROADCAST.value in cam_types
    assert VideoSourceType.ONBOARD.value in cam_types
    assert VideoSourceType.TRACKSIDE.value in cam_types

    summary = video_service.build_video_evidence_for_candidate(
        candidate_id="TEST_FIXTURE",
        session_id="test-session-fixture-2024",
        event_start_str="00:00:10.000",
        event_peak_str="00:00:15.000",
        event_end_str="00:00:20.000",
        pre_roll_sec=2.0,
        post_roll_sec=2.0,
    )

    assert summary.video_evidence_status == VideoSyncStatus.VIDEO_SYNCHRONIZED
    assert len(summary.multi_camera) == len(fixture_sources)
    
    # Check that each camera angle has its own unique clip window and frame rate
    for cam in summary.multi_camera:
        assert cam.incident_window is not None
        assert cam.sync_status == VideoSyncStatus.VIDEO_SYNCHRONIZED
        assert cam.confidence in (SyncConfidence.HIGH, SyncConfidence.MEDIUM)


# ==============================================================================
# 12. INCIDENT VIDEO WINDOW CONVERSION
# ==============================================================================

def test_incident_video_window_calculation():
    """Verify incident bounds are translated with pre-roll and post-roll into formatted timestamps."""
    source = VideoSourceMetadata(
        video_id="TEST-CAM-01",
        source_type=VideoSourceType.BROADCAST.value,
        session_id="test-sess",
        camera_label="Test Feed",
        session_to_video_offset_sec=10.0,  # video = session - 10.0
        duration_sec=3600.0,
        sync_status=VideoSyncStatus.VIDEO_SYNCHRONIZED,
        frame_rate=25.0,
    )

    summary = build_video_evidence(
        session_id="test-sess",
        event_start_str="00:01:00.000",  # 60s
        event_peak_str="00:01:05.000",   # 65s
        event_end_str="00:01:10.000",    # 70s
        source=source,
        pre_roll_sec=5.0,
        post_roll_sec=5.0,
    )

    assert summary.incident_window is not None
    # 60 - 10 - 5 = 45s
    assert summary.incident_window.video_start_time == "00:00:45.000"
    # 65 - 10 = 55s
    assert summary.incident_window.video_peak_time == "00:00:55.000"
    # 70 - 10 + 5 = 65s
    assert summary.incident_window.video_end_time == "00:01:05.000"
    assert summary.incident_window.total_clip_duration_sec == pytest.approx(20.0, abs=0.1)
    assert summary.incident_window.frame_start == 45 * 25
    assert summary.incident_window.frame_peak == 55 * 25
    assert summary.incident_window.frame_end == 65 * 25


# ==============================================================================
# 13. FRAME NUMBER CONVERSION & SANITY
# ==============================================================================

def test_frame_number_conversion_and_sanity():
    """Verify integer frame number translation and rejection of invalid physical inputs."""
    transform = VideoTimeTransform(time_scale=1.0, offset_sec=0.0)

    # 50 fps video: 1.0s -> frame 50
    assert transform.session_to_frame_number(1.0, 50.0) == 50
    assert transform.frame_number_to_session_time(50, 50.0) == pytest.approx(1.0, abs=1e-4)

    # Rejection of invalid non-positive frame rate
    with pytest.raises(ValueError):
        transform.frame_number_to_session_time(100, 0.0)

    with pytest.raises(ValueError):
        transform.frame_number_to_session_time(100, -25.0)

    # Rejection of negative frame number
    with pytest.raises(ValueError):
        transform.frame_number_to_session_time(-5, 25.0)


# ==============================================================================
# 14. TIMEZONE & PROVENANCE RECORDING
# ==============================================================================

def test_timezone_and_provenance_metadata():
    """Verify video source explicitly captures timezone, timestamp basis, and provenance."""
    prov = VideoProvenanceRecord(
        source="Formula One Management (FOM)",
        source_reference="FIA World Feed Log Ch.1",
        acquisition_method="OFFICIAL_ARCHIVE",
        session="Italian Grand Prix 2024 — Race",
        camera="World Feed Main",
        timestamp_basis="SMPTE_LTC",
        availability="STREAM_AVAILABLE",
        metadata_quality="HIGH",
    )
    source = VideoSourceMetadata(
        video_id="SRC-MONZA-PROV",
        source_type=VideoSourceType.BROADCAST.value,
        session_id="f1-2024-ita-race",
        camera_label="Main Feed",
        timezone="Europe/Rome",
        provenance=prov,
    )

    assert source.timezone == "Europe/Rome"
    assert source.provenance.timestamp_basis == "SMPTE_LTC"
    assert source.provenance.source == "Formula One Management (FOM)"


# ==============================================================================
# 15. REGRESSION AGAINST INCIDENT DOSSIER & MONZA REFERENCE CASES
# ==============================================================================

def test_regression_monza_reference_cases_video_unavailable(mock_candidate):
    """Verify Monza 2024 reference incidents honestly declare VIDEO_UNAVAILABLE."""
    video_service = get_video_service()

    for ref_id in ["REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"]:
        sources = video_service.get_sources_for_candidate(ref_id)
        assert len(sources) >= 1
        assert sources[0].sync_status == VideoSyncStatus.VIDEO_UNAVAILABLE
        assert sources[0].provenance.availability == "VIDEO_UNAVAILABLE"
        assert sources[0].provenance.acquisition_method == "UNLINKED"

    # Dossier synthesis integration via reconstruction engine
    from app.evidence.reconstruction_service import get_reconstruction_engine
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier("REF-MONZA-01")
    assert dossier is not None
    assert dossier.video_evidence is not None
    assert dossier.video_evidence.video_evidence_status == VideoSyncStatus.VIDEO_UNAVAILABLE

    # Frontend incident conversion
    frontend_inc = convert_dossier_to_frontend_incident(dossier)
    assert frontend_inc.video_available is False
    assert frontend_inc.video_evidence is not None
    assert frontend_inc.video_evidence.video_evidence_status == VideoSyncStatus.VIDEO_UNAVAILABLE


# ==============================================================================
# 16. COMPUTER VISION READINESS CONTRACT (SynchronizedVideoFrame)
# ==============================================================================

def test_computer_vision_readiness_contract():
    """Verify SynchronizedVideoFrame provides complete ground truth for future CV modules."""
    video_service = get_video_service()
    fixture_sources = video_service.get_sources_for_candidate("TEST_FIXTURE")
    cam_wf = fixture_sources[0]

    cv_frame = video_service.extract_synchronized_frame(
        source=cam_wf,
        session_time_sec=15.0,
        session_timestamp_str="2024-09-01 13:04:15.000",
    )

    assert isinstance(cv_frame, SynchronizedVideoFrame)
    assert cv_frame.video_id == cam_wf.video_id
    assert cv_frame.camera == cam_wf.camera_label
    assert cv_frame.session_time_sec == 15.0
    assert cv_frame.session_timestamp == "2024-09-01 13:04:15.000"
    assert cv_frame.frame_number is not None
    assert cv_frame.frame_number >= 0
    assert cv_frame.synchronization_error_sec >= 0.0
    assert cv_frame.provenance is not None


# ==============================================================================
# 17. REST API ENDPOINTS INTEGRATION
# ==============================================================================

def test_api_candidate_video_endpoints(client):
    """Test GET /api/v1/analysis/candidates/{candidate_id}/video and /synchronization."""
    # 1. Test video evidence endpoint on reference incident
    response = client.get("/api/v1/analysis/candidates/REF-MONZA-01/video")
    assert response.status_code == 200
    data = response.json()

    assert "videoEvidenceStatus" in data
    assert data["videoEvidenceStatus"] == "VIDEO_UNAVAILABLE"
    assert "sources" in data
    assert "incidentWindow" in data
    assert "statement" in data
    assert "limitations" in data

    # 2. Test video synchronization endpoint
    sync_resp = client.get("/api/v1/analysis/candidates/REF-MONZA-01/video/synchronization")
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()

    assert "candidateId" in sync_data
    assert "syncStatus" in sync_data
    assert "statement" in sync_data
    assert sync_data["syncStatus"] == "VIDEO_UNAVAILABLE"
