"""Comprehensive unit and integration tests for Reference-Lap Baseline and Evidence Quantification.

Validates:
1. Reference lap selection 7-rule filtering (incident lap, invalid laps, pit laps, pace outliers, proximity).
2. Uniform distance-grid resampling and alignment.
3. Robust pointwise median baseline computation & IQR variability.
4. Control disruption metrics (braking onset delta, apex speed delta, throttle reapplication delay).
5. Cartesian Euclidean trajectory deviation (SI meters, decimeter conversion fidelity).
6. Explicit signal provenance (OBSERVED, DERIVED, UNAVAILABLE).
7. Integration with candidate dossier and frontend contracts.
8. Evaluation against Monza 2024 reference cases.
"""

from datetime import datetime, timezone, timedelta
from typing import List
import numpy as np
import pytest

from app.data.domain import NormalizedLap, NormalizedTelemetryPoint
from app.evidence.baseline_models import (
    BaselineDisruptionMetrics,
    BaselineEvidence,
    BaselineStatus,
    DriverBaselineEvidence,
    SignalProvenanceInfo,
    SignalStatus,
    TrajectoryDeviationMetrics,
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
from app.services.baseline_service import ReferenceBaselineService, get_baseline_service


# --- Fixtures ---

@pytest.fixture
def baseline_service() -> ReferenceBaselineService:
    return ReferenceBaselineService()


def make_mock_laps(
    driver_code: str = "RIC",
    count: int = 15,
    incident_lap: int = 5,
    base_lap_time: float = 84.5,
) -> List[NormalizedLap]:
    """Synthesize a representative stint of lap timings."""
    laps: List[NormalizedLap] = []
    base_dt = datetime(2024, 9, 1, 13, 0, 0, tzinfo=timezone.utc)

    for i in range(1, count + 1):
        # Inject standard conditions or anomalies
        lap_time = base_lap_time + (i % 3) * 0.2
        is_valid = True

        if i == 1:
            # Out-lap / standing start: slow
            lap_time = 105.2
        elif i == 8:
            # Invalid lap limits
            is_valid = False
            lap_time = 83.9
        elif i == 12:
            # In-lap / pit stop
            lap_time = 112.4
        elif i == 14:
            # Virtual safety car pace anomaly
            lap_time = 120.0

        laps.append(
            NormalizedLap(
                driver_code=driver_code,
                driver_number=3,
                lap_number=i,
                lap_time_seconds=lap_time,
                sector_1_seconds=27.5,
                sector_2_seconds=28.5,
                sector_3_seconds=28.5,
                compound="MEDIUM",
                is_valid=is_valid,
                start_time=base_dt + timedelta(seconds=i * 90),
                source="test",
            )
        )
    return laps


def make_corner_telemetry(
    driver_code: str = "RIC",
    lap_number: int = 3,
    dist_start: float = 1200.0,
    dist_end: float = 1800.0,
    apex_speed: float = 140.0,
    brake_onset_m: float = 1350.0,
    lateral_offset_m: float = 0.0,
) -> List[NormalizedTelemetryPoint]:
    """Synthesize realistic cornering telemetry points through a braking and cornering zone."""
    pts: List[NormalizedTelemetryPoint] = []
    dists = np.arange(dist_start, dist_end + 2.0, 2.0)
    apex_dist = 1500.0

    for idx, d in enumerate(dists):
        # Kinematic profile: approach at 320 km/h, brake down to apex_speed, accelerate to 280 km/h
        if d < brake_onset_m:
            speed = 320.0 - (d - dist_start) * 0.05
            throttle = 100.0
            brake = 0.0
        elif d < apex_dist:
            # Braking zone
            progress = (d - brake_onset_m) / max(apex_dist - brake_onset_m, 1.0)
            speed = 310.0 - progress * (310.0 - apex_speed)
            throttle = 0.0
            brake = 100.0 if progress < 0.6 else 40.0
        else:
            # Corner exit acceleration
            exit_prog = (d - apex_dist) / max(dist_end - apex_dist, 1.0)
            speed = apex_speed + exit_prog * (280.0 - apex_speed)
            brake = 0.0
            throttle = min(100.0, exit_prog * 130.0)

        # Approximate 2D path (corner curve in SI meters)
        x = float(d) * 0.8
        y = math_curve_y(d, apex_dist) + lateral_offset_m

        pts.append(
            NormalizedTelemetryPoint(
                time_offset=idx * 0.1,
                driver_code=driver_code,
                lap_number=lap_number,
                distance=float(d),
                speed=float(speed),
                throttle=float(throttle),
                brake=float(brake),
                gear=3 if speed < 160 else 6,
                x=x,
                y=y,
                z=10.0,
            )
        )
    return pts


def math_curve_y(distance: float, apex_dist: float) -> float:
    """Helper to generate curved trajectory profile."""
    rel = (distance - apex_dist) / 300.0
    return 500.0 + 40.0 * (1.0 - rel**2) if abs(rel) <= 1.0 else 500.0


# --- Unit Tests ---

def test_reference_lap_selection_strict_rules(baseline_service):
    """Verify reference lap selection strictly implements the 7 filtering criteria."""
    laps = make_mock_laps(driver_code="RIC", count=15, incident_lap=5, base_lap_time=84.5)

    valid_laps, exclusions = baseline_service.filter_reference_laps(laps, incident_lap=5)

    # 1. Incident lap (5) must be excluded
    assert "Lap 5" in exclusions
    assert "Incident lap" in exclusions["Lap 5"]
    assert all(l.lap_number != 5 for l in valid_laps)

    # 2. Out-lap (1) must be excluded due to pace anomaly
    assert "Lap 1" in exclusions

    # 3. Invalid lap limits (8) must be excluded
    assert "Lap 8" in exclusions
    assert "invalidated" in exclusions["Lap 8"].lower()

    # 4. In-lap / pit transit (12) must be excluded
    assert "Lap 12" in exclusions

    # 5. Pace anomaly (14) must be excluded
    assert "Lap 14" in exclusions

    # 6. Must contain clean laps within proximity window
    valid_numbers = [l.lap_number for l in valid_laps]
    assert len(valid_numbers) >= 2
    assert 2 in valid_numbers or 3 in valid_numbers or 4 in valid_numbers or 6 in valid_numbers


def test_reference_lap_insufficient_data(baseline_service):
    """Verify that fewer than 2 valid laps returns INSUFFICIENT_REFERENCE_DATA."""
    # Only 1 lap
    single_lap = [
        NormalizedLap(
            driver_code="RIC",
            driver_number=3,
            lap_number=1,
            lap_time_seconds=85.0,
            is_valid=True,
        )
    ]
    evidence = baseline_service.quantify_driver(
        driver_code="RIC",
        incident_lap=1,
        incident_points=[],
        session_laps=single_lap,
        season=2024,
        round_or_name="Monza",
        session_identifier="Race",
    )
    assert evidence.status == BaselineStatus.INSUFFICIENT_REFERENCE_DATA
    assert evidence.disruption_metrics is None
    assert evidence.trajectory_metrics is None


def test_distance_grid_alignment(baseline_service):
    """Verify telemetry interpolation onto a uniform 2.0m distance grid."""
    pts = make_corner_telemetry(dist_start=1200.0, dist_end=1500.0)
    aligned = baseline_service.align_telemetry_on_distance(pts, s_start=1200.0, s_end=1500.0, step_m=2.0)

    assert aligned is not None
    grid = aligned["distance"]
    assert len(grid) == 151  # (1500 - 1200) / 2 + 1
    assert grid[0] == 1200.0
    assert grid[-1] == 1500.0
    assert aligned["speed"].shape == grid.shape
    assert aligned["throttle"].shape == grid.shape
    assert aligned["brake"].shape == grid.shape
    assert aligned["x"].shape == grid.shape
    assert aligned["has_coords"] is True


def test_robust_median_baseline_computation(baseline_service):
    """Verify pointwise median and IQR variability across multiple reference laps."""
    lap2 = make_corner_telemetry(lap_number=2, apex_speed=142.0)
    lap3 = make_corner_telemetry(lap_number=3, apex_speed=140.0)
    lap4 = make_corner_telemetry(lap_number=4, apex_speed=138.0)

    al2 = baseline_service.align_telemetry_on_distance(lap2, 1300.0, 1700.0, step_m=2.0)
    al3 = baseline_service.align_telemetry_on_distance(lap3, 1300.0, 1700.0, step_m=2.0)
    al4 = baseline_service.align_telemetry_on_distance(lap4, 1300.0, 1700.0, step_m=2.0)

    grid = al2["distance"]
    baseline = baseline_service.compute_median_baseline([al2, al3, al4], grid)

    assert baseline["distance"].shape == grid.shape
    # Median apex speed should be 140.0 km/h (median of 138, 140, 142)
    apex_idx = np.argmin(baseline["speed"])
    assert abs(baseline["speed"][apex_idx] - 140.0) < 0.5
    # Speed IQR should be non-negative
    assert (baseline["speed_iqr"] >= 0.0).all()


def test_disruption_metrics_quantification(baseline_service):
    """Verify braking onset, apex speed delta, and throttle reapplication calculations."""
    ref_laps = [
        make_corner_telemetry(lap_number=i, apex_speed=140.0, brake_onset_m=1350.0)
        for i in [2, 3, 4]
    ]
    # Incident lap: driver braked 15m later (1365m), hit apex 12 km/h slower (128 km/h)
    inc_lap = make_corner_telemetry(lap_number=5, apex_speed=128.0, brake_onset_m=1365.0)

    al_refs = [baseline_service.align_telemetry_on_distance(l, 1300.0, 1700.0, step_m=2.0) for l in ref_laps]
    al_inc = baseline_service.align_telemetry_on_distance(inc_lap, 1300.0, 1700.0, step_m=2.0)

    baseline = baseline_service.compute_median_baseline(al_refs, al_refs[0]["distance"])
    disruption = baseline_service.compute_disruption_metrics(baseline, al_inc, "RIC")

    assert disruption.driver_code == "RIC"
    # Apex speed was slower: delta must be negative (-12.0 km/h)
    assert disruption.min_corner_speed_delta_kmh is not None
    assert disruption.min_corner_speed_delta_kmh < -5.0
    assert disruption.speed_at_apex_incident_kmh == 128.0
    assert abs(disruption.speed_at_apex_baseline_kmh - 140.0) < 1.0

    # Braking onset delta should be positive (braked later in distance)
    assert disruption.braking_onset_delta_m is not None
    assert disruption.braking_onset_delta_m > 0.0


def test_trajectory_deviation_meters_fidelity(baseline_service):
    """Verify Cartesian 2D Euclidean trajectory deviation maintains decimeter->meter SI fidelity."""
    ref_laps = [
        make_corner_telemetry(lap_number=i, lateral_offset_m=0.0)
        for i in [2, 3, 4]
    ]
    # Incident lap: forced/ran 1.75 meters wide
    inc_lap = make_corner_telemetry(lap_number=5, lateral_offset_m=1.75)

    al_refs = [baseline_service.align_telemetry_on_distance(l, 1300.0, 1700.0, step_m=2.0) for l in ref_laps]
    al_inc = baseline_service.align_telemetry_on_distance(inc_lap, 1300.0, 1700.0, step_m=2.0)

    baseline = baseline_service.compute_median_baseline(al_refs, al_refs[0]["distance"])
    traj = baseline_service.compute_trajectory_deviation(baseline, al_inc, "RIC")

    assert traj.status == SignalStatus.DERIVED
    assert traj.lateral_track_deviation_status == SignalStatus.UNAVAILABLE
    # Max deviation should be around 1.75 meters (SI meters, NOT 17.5 decimeters or 1750 millimeters)
    assert 1.70 <= traj.max_trajectory_deviation_m <= 1.80
    assert 1.70 <= traj.mean_trajectory_deviation_m <= 1.80
    assert traj.deviation_at_apex_m is not None
    assert 1.70 <= traj.deviation_at_apex_m <= 1.80


def test_signal_provenance_explicit_catalog():
    """Verify explicit distinction between OBSERVED, DERIVED, and UNAVAILABLE signals."""
    info = SignalProvenanceInfo()
    assert info.speed == SignalStatus.OBSERVED
    assert info.throttle == SignalStatus.OBSERVED
    assert info.brake == SignalStatus.OBSERVED
    assert info.gear == SignalStatus.OBSERVED
    assert info.rpm == SignalStatus.OBSERVED

    # Derived
    assert info.longitudinal_accel == SignalStatus.DERIVED
    assert info.trajectory_deviation == SignalStatus.DERIVED

    # Explicitly unavailable in standard FastF1 telemetry
    assert info.steering == SignalStatus.UNAVAILABLE
    assert info.brake_pressure_bar == SignalStatus.UNAVAILABLE
    assert info.track_relative_lateral == SignalStatus.UNAVAILABLE


def test_synthesize_baseline_evidence_integration():
    """Verify full baseline evidence synthesis integration with candidate dossier."""
    # Synthesize frames for candidate
    frames: List[TelemetryPointSchema] = []
    base_dt = 13 * 3600 + 4 * 60 + 10.0
    for i in range(50):
        t_sec = base_dt + i * 0.04
        frames.append(
            TelemetryPointSchema(
                time_offset=round(i * 0.04, 3),
                timestamp=f"2024-09-01 13:04:{10.0 + i * 0.04:06.3f}",
                speed_a=220.0 - i * 0.5,
                speed_b=225.0 - i * 0.55,
                throttle_a=20.0 if i < 15 else 0.0,
                throttle_b=30.0 if i < 15 else 0.0,
                brake_a=80.0 if i >= 15 else 0.0,
                brake_b=90.0 if i >= 15 else 0.0,
                steer_a=5.0,
                steer_b=-2.0,
                gear_a=4,
                gear_b=4,
                accel_a=-2.5 if i >= 15 else 0.2,
                accel_b=-2.8 if i >= 15 else 0.3,
                distance_a=round(1400.0 + i * 2.2, 2),
                distance_b=round(1400.0 + i * 2.2 + 1.5, 2),
                lap_number_a=5,
                lap_number_b=5,
                speed_difference=-5.0,
                gap_meters=1.5,
                closing_speed_ms=3.0,
                lateral_dist_meters=1.2,
                same_lap=True,
            )
        )

    cand = CandidateDossier(
        candidate_id="CAND-2024-MON-RIC_HUL-L5-01",
        session_id="f1-2024-italian grand prix-race",
        driver_a="RIC",
        driver_b="HUL",
        lap_number_a=5,
        lap_number_b=5,
        event_start=frames[0].timestamp,
        event_peak=frames[25].timestamp,
        event_end=frames[-1].timestamp,
        duration_seconds=2.0,
        event_type=CandidateEventType.CONTACT_CANDIDATE,
        status=CandidateStatus.PENDING_REVIEW,
        evidence_strength=85,
        turn="Turn 4",
        minimum_gap_meters=1.5,
        peak_closing_speed_ms=5.0,
        speed_delta_at_peak=-5.0,
        speed_a_at_peak=207.5,
        speed_b_at_peak=212.5,
        braking_change={"decel_delta_g": 0.3},
        data_quality_flags=DataQualityFlags(),
    )

    dossier = synthesize_incident_evidence_dossier(
        candidate=cand,
        raw_frames=frames,
        all_features=[],
    )

    assert dossier is not None
    assert hasattr(dossier, "baseline_evidence")
    
    # Convert to frontend incident
    frontend_inc = convert_dossier_to_frontend_incident(dossier)
    assert frontend_inc.id == cand.candidate_id
    assert hasattr(frontend_inc, "baseline_evidence")
    # Verified evidence assessments
    assert len(frontend_inc.evidence_assessment) >= 2


def test_monza_reference_cases_provenance():
    """Verify Monza reference cases have structured baseline representations."""
    from app.evidence.evaluation import MONZA_2024_REFERENCE_CASES
    assert len(MONZA_2024_REFERENCE_CASES) >= 3

    case_laps = {ref.case_id: ref.lap for ref in MONZA_2024_REFERENCE_CASES}
    assert case_laps["REF-MONZA-01"] == 1
    assert case_laps["REF-MONZA-02"] == 4
    assert case_laps["REF-MONZA-03"] == 19


def test_api_candidate_baseline_endpoint(client):
    """Verify GET /api/v1/analysis/candidates/{candidate_id}/baseline endpoint."""
    resp = client.get("/api/v1/analysis/candidates/REF-MONZA-01/baseline")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "drivers" in data
    assert "signalProvenance" in data
    assert "stewardGuidance" in data
    assert data["signalProvenance"]["speed"] == "OBSERVED"
    assert data["signalProvenance"]["steering"] == "UNAVAILABLE"
    assert data["signalProvenance"]["trajectoryDeviation"] == "DERIVED"


def test_api_candidate_frontend_incident_includes_baseline(client):
    """Verify GET /api/v1/analysis/candidates/{candidate_id}/frontend-incident includes baseline."""
    resp = client.get("/api/v1/analysis/candidates/REF-MONZA-01/frontend-incident")
    assert resp.status_code == 200
    data = resp.json()
    assert "baselineEvidence" in data
    assert data["baselineEvidence"] is not None

