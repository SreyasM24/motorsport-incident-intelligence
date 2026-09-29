"""Unit and integration tests for multi-modal evidence dossier synthesis.

Validates:
1. Telemetry evidence extraction & empirical metrics.
2. Chronological timeline milestone generation.
3. Race control message correlation & relative delta-t calculation.
4. Video synchronization metadata & clip boundary recommendations.
5. Statutory regulation matching & evidence linkages.
6. Decoupled evidence dimensions (telemetry, race control, video, regulations).
7. Frontend IncidentDetailResponse contract transformation.
8. API endpoints for candidate dossiers and frontend-incident detail.
"""

import pytest
from app.evidence.candidate import (
    CandidateDossier,
    CandidateEventType,
    CandidateStatus,
    DataQualityFlags,
)
from app.evidence.dossier import (
    EvidenceDimensions,
    IncidentEvidenceDossier,
    convert_dossier_to_frontend_incident,
    synthesize_incident_evidence_dossier,
)
from app.evidence.features import FrameFeatures, extract_pairwise_features
from app.evidence.race_control_evidence import (
    RaceControlEvidenceSummary,
    RaceControlMessageEvidence,
    build_race_control_evidence,
)
from app.evidence.regulation_evidence import (
    RegulationEvidenceSummary,
    match_relevant_regulations,
)
from app.evidence.telemetry_evidence import (
    TelemetryEvidenceSummary,
    build_telemetry_evidence,
)
from app.evidence.timeline import TimelineMilestone, generate_event_timeline
from app.evidence.video_evidence import (
    VideoClipRecommendation,
    VideoEvidenceSummary,
    VideoSourceMetadata,
    VideoSyncStatus,
    build_video_evidence,
    format_seconds_to_time,
)
from app.schemas.telemetry import TelemetryPointSchema


# --- Fixtures ---

@pytest.fixture
def sample_telemetry_frames():
    """Create a synthetic sequence of 25Hz synchronized telemetry points."""
    frames = []
    base_time = 13 * 3600 + 4 * 60 + 10.0  # 13:04:10.000
    for i in range(100):  # 4.0 seconds at 25Hz
        t_sec = base_time + i * 0.04
        h = int(t_sec // 3600)
        m = int((t_sec % 3600) // 60)
        s = t_sec % 60
        ts_str = f"2024-09-01 {h:02d}:{m:02d}:{s:06.3f}"
        
        # Simulate convergence to a minimum gap at frame 50
        dist_from_peak = abs(i - 50)
        gap = 1.20 + dist_from_peak * 0.15

        frame = TelemetryPointSchema(
            time_offset=round(i * 0.04, 3),
            timestamp=ts_str,
            speed_a=round(240.0 - i * 0.8, 1),
            speed_b=round(245.0 - i * 0.85, 1),
            throttle_a=10.0 if i < 30 else 0.0,
            throttle_b=15.0 if i < 30 else 0.0,
            brake_a=85.0 if i >= 30 else 0.0,
            brake_b=95.0 if i >= 30 else 0.0,
            steer_a=12.5,
            steer_b=-4.0,
            gear_a=5,
            gear_b=5,
            accel_a=-3.2 if i >= 30 else 0.5,
            accel_b=-3.5 if i >= 30 else 0.6,
            distance_a=round(1000.0 + i * 2.5, 2),
            distance_b=round(1000.0 + i * 2.5 + gap, 2),
            lap_number_a=1,
            lap_number_b=1,
            speed_difference=round((240.0 - i * 0.8) - (245.0 - i * 0.85), 1),
            gap_meters=round(gap, 2),
            closing_speed_ms=round(5.0 - (i - 50) * 0.2, 2),
            lateral_dist_meters=round(gap * 0.9, 2),
            same_lap=True,
        )
        frames.append(frame)
    return frames


@pytest.fixture
def sample_features(sample_telemetry_frames):
    """Create pairwise features corresponding to sample frames."""
    return extract_pairwise_features(sample_telemetry_frames, dt_sec=0.04)


@pytest.fixture
def sample_candidate(sample_telemetry_frames):
    """Create a sample CandidateDossier."""
    start_ts = sample_telemetry_frames[20].timestamp
    peak_ts = sample_telemetry_frames[50].timestamp
    end_ts = sample_telemetry_frames[80].timestamp

    return CandidateDossier(
        candidate_id="CAND-2024-MON-RIC_HUL-L1-01",
        session_id="f1-2024-italian grand prix-race",
        driver_a="RIC",
        driver_b="HUL",
        lap_number_a=1,
        lap_number_b=1,
        event_start=start_ts,
        event_peak=peak_ts,
        event_end=end_ts,
        duration_seconds=2.4,
        event_type=CandidateEventType.CONTACT_CANDIDATE,
        status=CandidateStatus.PENDING_REVIEW,
        evidence_strength=88,
        turn="Turn 4",
        minimum_gap_meters=1.20,
        peak_closing_speed_ms=8.5,
        speed_delta_at_peak=-5.0,
        speed_a_at_peak=200.0,
        speed_b_at_peak=205.0,
        braking_change={"driver_a_brake": 85.0, "driver_b_brake": 95.0, "decel_delta_g": 0.3},
        trajectory_change={"driver_a_yaw": 0.5, "driver_b_yaw": 0.6},
        evidence_signals=[],
        race_control_context=[],
        data_quality_flags=DataQualityFlags(),
        summary="RIC and HUL converged to 1.20m minimum proximity in Turn 4 braking zone.",
        detection_method="Multi-signal kinematic and spatial threshold convergence",
    )


# --- Tests ---

def test_build_telemetry_evidence(sample_telemetry_frames):
    """Test telemetry evidence summary calculation."""
    summary = build_telemetry_evidence(
        driver_a="RIC",
        driver_b="HUL",
        raw_frames=sample_telemetry_frames,
        start_index=20,
        peak_index=50,
        end_index=80,
        evidence_strength=88,
    )
    assert isinstance(summary, TelemetryEvidenceSummary)
    assert summary.driver_a == "RIC"
    assert summary.driver_b == "HUL"
    assert summary.minimum_gap_meters == pytest.approx(1.20, abs=0.05)
    assert summary.duration_seconds == pytest.approx(2.4, abs=0.1)
    assert summary.telemetry_evidence_strength == 88
    assert summary.total_frames == 61
    assert "FastF1" in summary.raw_stream_ref or summary.total_frames > 0


def test_generate_event_timeline(sample_features):
    """Test chronological milestone generation."""
    milestones = generate_event_timeline(
        features=sample_features,
        peak_offset=sample_features[50].time_offset,
        driver_a="RIC",
        driver_b="HUL",
    )
    assert len(milestones) >= 3
    labels = [m.label for m in milestones]
    assert any("Approach Phase" in l for l in labels)
    assert any("Apex" in l for l in labels)
    assert any("Exit" in l for l in labels)
    # Verify chronological ordering
    for i in range(len(milestones) - 1):
        assert milestones[i].timestamp <= milestones[i + 1].timestamp


def test_build_race_control_evidence():
    """Test race control evidence extraction and delta-t computation."""
    raw_messages = [
        {"utc": "2024-09-01T13:04:12Z", "message": "YELLOW FLAG IN SECTOR 2", "flag": "YELLOW"},
        {"utc": "2024-09-01T13:05:00Z", "message": "INCIDENT INVOLVING CARS 3 (RIC) AND 27 (HUL) NOTED", "flag": "CLEAR"},
    ]
    summary = build_race_control_evidence(
        raw_messages=raw_messages,
        peak_timestamp_str="2024-09-01 13:04:12.000",
        driver_a="RIC",
        driver_b="HUL",
    )
    assert isinstance(summary, RaceControlEvidenceSummary)
    assert len(summary.correlated_messages) == 2
    assert len(summary.active_flags) >= 1
    assert any(m.relative_time_to_peak_sec is None or abs(m.relative_time_to_peak_sec) < 120.0 for m in summary.correlated_messages)


def test_build_video_evidence_unavailable():
    """Test video evidence defaults to honest VIDEO_UNAVAILABLE when no verified source exists."""
    summary = build_video_evidence(
        session_id="f1-2024-italian grand prix-race",
        event_start_str="2024-09-01 13:04:10.000",
        event_peak_str="2024-09-01 13:04:12.000",
        event_end_str="2024-09-01 13:04:14.000",
        source=None,
    )
    assert summary.video_evidence_status == VideoSyncStatus.VIDEO_UNAVAILABLE
    assert summary.sources == []
    assert summary.recommended_clip is None
    assert "No verified video broadcast stream is linked" in summary.statement


def test_build_video_evidence_synchronized():
    """Test video synchronization calculation when video metadata is present."""
    source = VideoSourceMetadata(
        video_id="VID-MONZA-T4-01",
        source_type="OFFICIAL_BROADCAST",
        source_url="/assets/monza_t4.mp4",
        session_id="f1-2024-italian grand prix-race",
        camera_label="Turn 4 Trackside CCTV",
        session_to_video_offset_sec=13 * 3600 + 4 * 60 + 0.0,  # 13:04:00 offset
        time_scale=1.0,
        sync_status=VideoSyncStatus.VIDEO_SYNCHRONIZED,
    )
    summary = build_video_evidence(
        session_id="f1-2024-italian grand prix-race",
        event_start_str="2024-09-01 13:04:10.000",
        event_peak_str="2024-09-01 13:04:12.000",
        event_end_str="2024-09-01 13:04:14.000",
        source=source,
        pre_roll_sec=5.0,
        post_roll_sec=5.0,
    )
    assert summary.video_evidence_status == VideoSyncStatus.VIDEO_SYNCHRONIZED
    assert len(summary.sources) == 1
    assert summary.recommended_clip is not None
    # 13:04:10 - 13:04:00 - 5s = 5s
    assert summary.recommended_clip.clip_start_video_time == "00:00:05.000"
    # 13:04:12 - 13:04:00 = 12s
    assert summary.recommended_clip.clip_peak_video_time == "00:00:12.000"
    # 13:04:14 - 13:04:00 + 5s = 19s
    assert summary.recommended_clip.clip_end_video_time == "00:00:19.000"
    assert summary.recommended_clip.total_clip_duration_sec == pytest.approx(14.0, abs=0.1)


def test_match_relevant_regulations():
    """Test statutory regulation matching and evidence linkage."""
    reg_summary = match_relevant_regulations(
        event_type=CandidateEventType.CONTACT_CANDIDATE,
        minimum_gap=1.20,
        decel_delta_g=2.5,
    )
    assert isinstance(reg_summary, RegulationEvidenceSummary)
    assert len(reg_summary.references) >= 3
    articles = [r.article for r in reg_summary.references]
    assert "Article 33.4" in articles
    assert any("Chapter IV" in a for a in articles)

    # Verify neutral jurisprudential language
    for link in reg_summary.evidence_links:
        action = link.steward_review_action.lower()
        assert "guilty" not in action
        assert "penalty" not in action
        assert "infringement confirmed" not in action


def test_synthesize_incident_evidence_dossier(sample_candidate, sample_telemetry_frames, sample_features):
    """Test unified multi-modal dossier synthesis."""
    dossier = synthesize_incident_evidence_dossier(
        candidate=sample_candidate,
        raw_frames=sample_telemetry_frames,
        all_features=sample_features,
        session_rcm=[],
        video_source=None,
    )
    assert isinstance(dossier, IncidentEvidenceDossier)
    assert dossier.candidate_id == sample_candidate.candidate_id
    assert dossier.telemetry_evidence.minimum_gap_meters == pytest.approx(1.20, abs=0.05)
    assert len(dossier.timeline) > 0
    assert dossier.video_evidence.video_evidence_status == VideoSyncStatus.VIDEO_UNAVAILABLE
    assert len(dossier.regulation_evidence.references) >= 2
    assert "FastF1" in dossier.provenance["telemetry"].source

    # Check decoupled evidence dimensions
    dims = dossier.evidence_dimensions
    assert isinstance(dims, EvidenceDimensions)
    assert dims.telemetry_evidence_strength == 88
    assert dims.video_evidence_status == VideoSyncStatus.VIDEO_UNAVAILABLE


def test_convert_dossier_to_frontend_incident(sample_candidate, sample_telemetry_frames, sample_features):
    """Test transformation into frontend IncidentDetailResponse schema."""
    dossier = synthesize_incident_evidence_dossier(
        candidate=sample_candidate,
        raw_frames=sample_telemetry_frames,
        all_features=sample_features,
        session_rcm=[],
        video_source=None,
    )
    frontend_inc = convert_dossier_to_frontend_incident(dossier)
    assert frontend_inc.id == sample_candidate.candidate_id
    assert frontend_inc.driver_a == "RIC"
    assert frontend_inc.driver_b == "HUL"
    assert len(frontend_inc.evidence_assessment) >= 2
    assert len(frontend_inc.relevant_regulations) >= 2
    assert len(frontend_inc.evidence_connections) >= 2
    assert len(frontend_inc.timeline) >= 3
    assert frontend_inc.video_available is False
    assert len(frontend_inc.uncertainties) >= 1


def test_candidate_dossier_endpoint(client):
    """Test GET /api/v1/analysis/candidates/{candidate_id}/dossier endpoint."""
    res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/dossier")
    assert res.status_code == 200
    data = res.json()
    assert "dossierId" in data
    assert "candidate" in data
    assert "telemetryEvidence" in data
    assert "timeline" in data
    assert "videoEvidence" in data
    assert "regulationEvidence" in data
    assert "evidenceDimensions" in data
    assert data["videoEvidence"]["videoEvidenceStatus"] == "VIDEO_UNAVAILABLE"


def test_candidate_frontend_incident_endpoint(client):
    """Test GET /api/v1/analysis/candidates/{candidate_id}/frontend-incident endpoint."""
    res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/frontend-incident")
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert "driverA" in data
    assert "driverB" in data
    assert "evidenceAssessment" in data
    assert len(data["evidenceAssessment"]) >= 2
    assert "relevantRegulations" in data
    assert len(data["relevantRegulations"]) >= 2
    assert "evidenceConnections" in data
    assert len(data["evidenceConnections"]) >= 2
    assert "timeline" in data
    assert len(data["timeline"]) >= 3
