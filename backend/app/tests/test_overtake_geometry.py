"""Test suite for Cornering Overtake Geometry & Apex Overlap Analysis (Prompt 09).

Covers:
1. No overlap condition (gap > 5.63m)
2. Partial overlap condition (< 45%)
3. Approximately 50% overlap condition (45% - 55%)
4. Greater than 50% overlap condition (> 55%)
5. Insufficient geometry / missing coordinates handling
6. Corner phases detection (entry, apex min speed, exit recovery)
7. Exit clearance evaluation relative to 2.00m reference width
8. Vehicle longitudinal relative ordering (AHEAD, BEHIND, APPROXIMATELY_ALONGSIDE)
9. End-to-end evidence synthesis & provenance tracking
10. API endpoints (/overtake-geometry & /frontend-incident)
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.evidence.candidate import CandidateDossier, CandidateEventType, CandidateStatus
from app.schemas.overtake_geometry import (
    MeasurementConfidence,
    RelativeLongitudinalPosition,
    OverlapClassification,
    ExitClearanceClassification,
    CornerPhases,
    ApexOverlapSnapshot,
    ExitClearanceMetrics,
    OvertakeGeometryEvidence,
)
from app.schemas.telemetry import TelemetryPointSchema
from app.services.overtake_geometry_service import (
    CorneringOvertakeGeometryService,
    get_overtake_geometry_service,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def service():
    return get_overtake_geometry_service()


def create_synthetic_frames(
    n_points: int = 50,
    min_speed_idx: int = 25,
    speed_min: float = 120.0,
    speed_max: float = 280.0,
    delta_s_at_apex: float = 0.0,
    lateral_clearance_at_exit: float = 2.40,
) -> list[TelemetryPointSchema]:
    """Generate physically coherent synthetic cornering telemetry points for testing."""
    frames = []
    base_dist = 1000.0

    for i in range(n_points):
        # Progress parameter 0.0 -> 1.0
        t_norm = i / float(n_points - 1)
        # Distance monotonically increases
        s_a = base_dist + i * 4.0
        # Speed profile: deceleration into apex, acceleration out
        dist_from_apex = abs(i - min_speed_idx)
        norm_dist = dist_from_apex / float(max(min_speed_idx, n_points - 1 - min_speed_idx))
        speed_a = speed_min + (speed_max - speed_min) * (norm_dist ** 1.5)

        # Driver B follows with variable delta_s
        s_b = s_a - delta_s_at_apex
        speed_b = speed_a + (2.0 if i < min_speed_idx else -2.0)

        # X, Y coordinates modeling a 90-degree corner
        angle_rad = t_norm * 1.5708
        radius = 80.0
        x_a = radius * (1.0 - (1.0 - t_norm))
        y_a = radius * t_norm
        # Driver B slightly offset laterally
        lat_offset = 2.5 if i < min_speed_idx else lateral_clearance_at_exit
        x_b = x_a + lat_offset
        y_b = y_a

        throttle_a = 0.0 if i < min_speed_idx else (t_norm - 0.5) * 200.0
        brake_a = 100.0 * (1.0 - t_norm * 2.0) if i < min_speed_idx else 0.0

        ts_str = f"2024-09-01T13:00:{i*0.1:04.1f}Z"

        f = TelemetryPointSchema(
            time_offset=round(i * 0.1, 2),
            timestamp=ts_str,
            speed_a=round(speed_a, 2),
            throttle_a=round(max(0.0, min(100.0, throttle_a)), 1),
            brake_a=round(max(0.0, min(100.0, brake_a)), 1),
            gear_a=3,
            steer_a=15.0 if i == min_speed_idx else 5.0,
            accel_a=0.0,
            x_a=round(x_a, 2),
            y_a=round(y_a, 2),
            distance_a=round(s_a, 2),
            speed_b=round(speed_b, 2),
            throttle_b=round(max(0.0, min(100.0, throttle_a)), 1),
            brake_b=round(max(0.0, min(100.0, brake_a)), 1),
            gear_b=3,
            steer_b=15.0 if i == min_speed_idx else 5.0,
            accel_b=0.0,
            x_b=round(x_b, 2),
            y_b=round(y_b, 2),
            distance_b=round(s_b, 2),
            gap_meters=round(abs(s_a - s_b) + 1.5, 2),
            closing_speed_ms=0.0,
            lateral_dist_meters=round(lat_offset, 2),
        )
        frames.append(f)

    return frames


@pytest.fixture
def mock_candidate():
    return CandidateDossier(
        candidate_id="CAND-TEST-001",
        session_id="f1-2024-monza-race",
        driver_a="RIC",
        driver_b="HUL",
        lap_number_a=1,
        lap_number_b=1,
        turn="Turn 4 (Variante della Roggia)",
        event_start="2024-09-01T13:00:00.0Z",
        event_peak="2024-09-01T13:00:02.5Z",
        event_end="2024-09-01T13:00:05.0Z",
        duration_seconds=2.5,
        event_type=CandidateEventType.MULTI_SIGNAL_INTERACTION,
        status=CandidateStatus.PENDING_REVIEW,
        summary="Empirical overtake attempt into Turn 4.",
        minimum_gap_meters=1.85,
        peak_closing_speed_ms=4.2,
        speed_delta_at_peak=0.0,
        speed_a_at_peak=120.0,
        speed_b_at_peak=120.0,
        evidence_strength=88,
        detection_method="KINEMATIC_INTERACTION",
    )


# ==============================================================================
# 1. OVERLAP CLASSIFICATION THRESHOLD TESTS
# ==============================================================================

def test_no_measurable_overlap(service):
    """When longitudinal gap delta_s >= 5.63m, overlap must be 0% and NO_MEASURABLE_OVERLAP."""
    ratio, pct, classification = service.calculate_overlap(delta_s_m=6.00)
    assert classification == OverlapClassification.NO_MEASURABLE_OVERLAP
    assert ratio == 0.0
    assert pct == 0.0


def test_partial_overlap(service):
    """When gap is between 3.10m and 5.63m (overlap < 45%), classification is PARTIAL_OVERLAP."""
    # delta_s = 4.0m -> overlap = (5.63 - 4.0)/5.63 = 1.63 / 5.63 ~ 28.95%
    ratio, pct, classification = service.calculate_overlap(delta_s_m=4.00)
    assert classification == OverlapClassification.PARTIAL_OVERLAP
    assert 0.0 < pct < 45.0
    assert round(ratio * 100.0, 1) == round(pct, 1)


def test_approximately_50_percent_overlap(service):
    """When overlap is in [45.0%, 55.0%], classification is APPROXIMATELY_50_PERCENT_OVERLAP."""
    # delta_s = 2.815m -> overlap = 50.0%
    ratio, pct, classification = service.calculate_overlap(delta_s_m=2.815)
    assert classification == OverlapClassification.APPROXIMATELY_50_PERCENT_OVERLAP
    assert 45.0 <= pct <= 55.0


def test_greater_than_50_percent_overlap(service):
    """When overlap > 55.0%, classification is GREATER_THAN_50_PERCENT_OVERLAP."""
    # delta_s = 1.0m -> overlap = 4.63 / 5.63 = 82.2%
    ratio, pct, classification = service.calculate_overlap(delta_s_m=1.00)
    assert classification == OverlapClassification.GREATER_THAN_50_PERCENT_OVERLAP
    assert pct > 55.0


def test_perfect_alignment_full_overlap(service):
    """When delta_s = 0.0m (cars fully abreast), overlap is 100%."""
    ratio, pct, classification = service.calculate_overlap(delta_s_m=0.0)
    assert classification == OverlapClassification.GREATER_THAN_50_PERCENT_OVERLAP
    assert ratio == 1.0
    assert pct == 100.0


# ==============================================================================
# 2. RELATIVE LONGITUDINAL ORDERING TESTS
# ==============================================================================

def test_relative_longitudinal_ordering(service):
    """Verify strictly factual longitudinal position categorization."""
    # Incident car ahead
    delta_s_a, _, rel_ahead = service.calculate_vehicle_relationship(delta_s_m=2.5)
    assert rel_ahead == RelativeLongitudinalPosition.AHEAD
    assert delta_s_a == 2.5

    # Incident car behind
    delta_s_b, _, rel_behind = service.calculate_vehicle_relationship(delta_s_m=-2.5)
    assert rel_behind == RelativeLongitudinalPosition.BEHIND
    assert delta_s_b == -2.5

    # Approximately alongside (|delta_s| <= 0.5m)
    delta_s_c, _, rel_alongside = service.calculate_vehicle_relationship(delta_s_m=0.3)
    assert rel_alongside == RelativeLongitudinalPosition.APPROXIMATELY_ALONGSIDE
    assert delta_s_c == 0.3


# ==============================================================================
# 3. CORNER PHASES & EXIT CLEARANCE TESTS
# ==============================================================================

def test_corner_phase_detection(service):
    """Corner entry, apex (min speed), and exit recovery are correctly segmented."""
    frames = create_synthetic_frames(n_points=40, min_speed_idx=20, speed_min=115.0, speed_max=270.0)
    phases = service.detect_corner_phases(frames)

    assert phases.apex_distance_m > phases.corner_entry_distance_m
    assert phases.apex_speed_kmh == pytest.approx(113.0, abs=3.0)
    assert phases.apex_detection_method == "MINIMUM_CORNER_SPEED"
    assert phases.corner_exit_distance_m is not None
    assert phases.corner_exit_distance_m >= phases.apex_distance_m


def test_exit_clearance_metrics(service):
    """Clearance evaluated against 2.00m reference width."""
    # Clearance above reference (> 2.10m)
    frames_wide = create_synthetic_frames(n_points=30, min_speed_idx=15, lateral_clearance_at_exit=2.50)
    phases_wide = service.detect_corner_phases(frames_wide)
    clearance_above = service.calculate_exit_clearance(frames_wide, phases_wide)
    assert clearance_above.clearance_classification == ExitClearanceClassification.CLEARANCE_ABOVE_REFERENCE
    assert clearance_above.measured_clearance_m == pytest.approx(2.50, abs=0.1)

    # Clearance near reference (1.90m to 2.10m)
    frames_near = create_synthetic_frames(n_points=30, min_speed_idx=15, lateral_clearance_at_exit=2.00)
    phases_near = service.detect_corner_phases(frames_near)
    clearance_near = service.calculate_exit_clearance(frames_near, phases_near)
    assert clearance_near.clearance_classification == ExitClearanceClassification.CLEARANCE_NEAR_REFERENCE

    # Clearance below reference (< 1.90m)
    frames_below = create_synthetic_frames(n_points=30, min_speed_idx=15, lateral_clearance_at_exit=1.40)
    phases_below = service.detect_corner_phases(frames_below)
    clearance_below = service.calculate_exit_clearance(frames_below, phases_below)
    assert clearance_below.clearance_classification == ExitClearanceClassification.CLEARANCE_BELOW_REFERENCE


# ==============================================================================
# 4. MISSING DATA & FAULT TOLERANCE TESTS
# ==============================================================================

def test_missing_positional_coordinates_graceful_fallback(service, mock_candidate):
    """If X, Y or distance coordinates are missing/zero, synthesize returns limited/partial confidence."""
    # Create frames with no distance and missing X/Y
    empty_frames = [
        TelemetryPointSchema(
            time_offset=float(i) * 0.1,
            timestamp=f"2024-09-01T13:00:{i*0.1:04.1f}Z",
            speed_a=180.0 - i * 5.0,
            throttle_a=0.0,
            brake_a=50.0,
            gear_a=4,
            steer_a=0.0,
            accel_a=0.0,
            speed_b=185.0 - i * 5.0,
            throttle_b=0.0,
            brake_b=50.0,
            gear_b=4,
            steer_b=0.0,
            accel_b=0.0,
            distance_a=0.0,
            distance_b=0.0,
            gap_meters=0.0,
            closing_speed_ms=0.0,
            x_a=None,
            y_a=None,
            x_b=None,
            y_b=None,
        )
        for i in range(15)
    ]

    evidence = service.synthesize_overtake_geometry(mock_candidate, empty_frames)
    assert evidence is not None
    assert evidence.overlap_classification in (
        OverlapClassification.INSUFFICIENT_GEOMETRIC_DATA,
        OverlapClassification.OVERLAP_ANALYSIS_LIMITED,
        OverlapClassification.NO_MEASURABLE_OVERLAP,
    )
    assert evidence.data_quality.missing_telemetry is True


def test_empty_frames_handling(service, mock_candidate):
    """Empty frames list returns graceful minimal fallback evidence without raising exceptions."""
    evidence = service.synthesize_overtake_geometry(mock_candidate, [])
    assert evidence is not None
    assert evidence.overlap_classification == OverlapClassification.INSUFFICIENT_GEOMETRIC_DATA
    assert evidence.data_quality.missing_telemetry is True


# ==============================================================================
# 5. END-TO-END EVIDENCE DOSSIER INTEGRATION & API TESTS
# ==============================================================================

def test_end_to_end_synthesis(service, mock_candidate):
    """Full synthesis populates corner phases, apex snapshot, clearance, and milestones."""
    frames = create_synthetic_frames(n_points=40, min_speed_idx=20, delta_s_at_apex=1.5, lateral_clearance_at_exit=2.4)
    evidence = service.synthesize_overtake_geometry(mock_candidate, frames)

    assert evidence.incident_id == mock_candidate.candidate_id
    assert evidence.driver_incident == mock_candidate.driver_a
    assert evidence.driver_other == mock_candidate.driver_b
    assert evidence.apex_snapshot is not None
    assert evidence.apex_snapshot.overlap_percent is not None
    assert evidence.exit_clearance.clearance_classification == ExitClearanceClassification.CLEARANCE_ABOVE_REFERENCE
    assert len(evidence.phase_snapshots) > 0
    assert evidence.fia_reference.rule_source == "FIA Formula One Driving Standards Guidelines"


def test_api_overtake_geometry_endpoint(client):
    """Test GET /api/v1/analysis/candidates/{candidate_id}/overtake-geometry."""
    # First reconstruct candidate or query reference case
    response = client.get("/api/v1/analysis/candidates/REF-MONZA-01/overtake-geometry")
    assert response.status_code == 200
    data = response.json()
    assert "apexSnapshot" in data
    assert "cornerPhases" in data
    assert "exitClearance" in data
    assert "overlapClassification" in data
    assert data["driverIncident"] == "RIC"
    assert data["driverOther"] == "HUL"


def test_api_frontend_incident_includes_overtake_geometry(client):
    """Test that frontend-incident response includes overtakeGeometry field and geometry evidence items."""
    response = client.get("/api/v1/analysis/candidates/REF-MONZA-01/frontend-incident")
    assert response.status_code == 200
    data = response.json()
    assert "overtakeGeometry" in data
    assert data["overtakeGeometry"] is not None
    assert data["overtakeGeometry"]["driverIncident"] == "RIC"

    # Verify that GEOMETRY category items were added to evidenceAssessment
    geom_items = [item for item in data["evidenceAssessment"] if item.get("category") == "GEOMETRY"]
    assert len(geom_items) >= 1
