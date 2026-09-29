"""Deterministic unit and integration tests for incident candidate reconstruction."""

from datetime import datetime, timezone, timedelta
import pytest

from app.evidence.candidate import (
    CandidateEventType,
    CandidateStatus,
    DataQualityFlags,
    EvidenceSignal,
    EvidenceSignalType,
)
from app.evidence.detector import DetectorConfig, MultiSignalDetector
from app.evidence.evaluation import (
    MONZA_2024_REFERENCE_CASES,
    evaluate_candidates_against_ground_truth,
)
from app.evidence.event_builder import (
    build_candidate_dossier,
    classify_event_type,
    compute_evidence_strength,
)
from app.evidence.features import FrameFeatures, extract_pairwise_features
from app.evidence.segmenter import EpisodeSegmenter, SegmenterConfig, SegmentedEpisode
from app.schemas.telemetry import TelemetryPointSchema


def make_frame(
    offset_sec: float,
    gap: float = 25.0,
    closing: float = 0.0,
    speed_a: float = 250.0,
    speed_b: float = 250.0,
    throttle_a: float = 100.0,
    throttle_b: float = 100.0,
    brake_a: float = 0.0,
    brake_b: float = 0.0,
    same_lap: bool = True,
    lap_a: int = 10,
    lap_b: int = 10,
) -> TelemetryPointSchema:
    """Helper to synthesize deterministic telemetry frames."""
    base_time = datetime(2024, 9, 1, 13, 30, 0, tzinfo=timezone.utc)
    ts = (base_time + timedelta(seconds=offset_sec)).strftime("%H:%M:%S.%f")[:-3]

    return TelemetryPointSchema(
        time_offset=offset_sec,
        timestamp=ts,
        speed_a=speed_a,
        throttle_a=throttle_a,
        brake_a=brake_a,
        gear_a=7,
        accel_a=0.0,
        distance_a=offset_sec * 60.0,
        lap_number_a=lap_a,
        speed_b=speed_b,
        throttle_b=throttle_b,
        brake_b=brake_b,
        gear_b=7,
        accel_b=0.0,
        distance_b=offset_sec * 60.0 - gap,
        lap_number_b=lap_b,
        speed_difference=round(speed_a - speed_b, 2),
        gap_meters=gap,
        closing_speed_ms=closing,
        lateral_dist_meters=0.0,
        same_lap=same_lap,
    )


def test_single_trigger_does_not_create_candidate():
    """Verify that a single isolated signal (e.g. proximity alone without closing or braking) does NOT trigger."""
    detector = MultiSignalDetector()
    # Moderate proximity (8m), but 0 closing speed, no braking, normal racing
    feat = FrameFeatures(
        index=0,
        time_offset=1.0,
        timestamp="13:30:01.000",
        gap_meters=8.0,
        closing_speed_ms=0.5,
        speed_difference_kmh=2.0,
        speed_a_kmh=200.0,
        speed_b_kmh=198.0,
        accel_a_g=0.0,
        accel_b_g=0.0,
        decel_delta_g=0.0,
        throttle_a=100.0,
        throttle_b=100.0,
        brake_a=0.0,
        brake_b=0.0,
        brake_delta_pct=0.0,
        same_lap=True,
    )

    signals = detector.evaluate_frame(feat)
    # Only 1 signal (Spatial Proximity)
    assert len(signals) == 1
    assert signals[0].signal_type == EvidenceSignalType.SPATIAL_PROXIMITY

    # detect_candidate_frames requires min_coincident_signals >= 2
    triggered = detector.detect_candidate_frames([feat])
    assert len(triggered) == 0, "Single trigger must NOT trigger candidate detection alone"


def test_multi_signal_trigger_creates_candidate():
    """Verify coincident proximity, high closing rate, and braking response triggers candidate."""
    detector = MultiSignalDetector()
    feat = FrameFeatures(
        index=0,
        time_offset=1.0,
        timestamp="13:30:01.000",
        gap_meters=4.2,  # Critical proximity (< 5m)
        closing_speed_ms=9.5,  # High closing rate (> 6 m/s)
        speed_difference_kmh=35.0,
        speed_a_kmh=240.0,
        speed_b_kmh=205.0,
        accel_a_g=-2.8,  # Hard braking
        accel_b_g=-0.5,
        decel_delta_g=2.3,  # Decel delta (> 2G)
        throttle_a=0.0,
        throttle_b=80.0,
        brake_a=100.0,
        brake_b=0.0,
        brake_delta_pct=100.0,  # Asymmetric brake response
        same_lap=True,
    )

    signals = detector.evaluate_frame(feat)
    unique_types = {s.signal_type for s in signals}
    assert len(unique_types) >= 3

    triggered = detector.detect_candidate_frames([feat])
    assert len(triggered) == 1
    assert triggered[0].time_offset == 1.0


def test_normal_slipstream_filtered_out():
    """Verify normal high-speed slipstreaming on straights is rejected."""
    detector = MultiSignalDetector()
    feat = FrameFeatures(
        index=0,
        time_offset=5.0,
        timestamp="13:30:05.000",
        gap_meters=14.0,
        closing_speed_ms=8.0,  # Approaching in slipstream
        speed_difference_kmh=28.0,
        speed_a_kmh=320.0,
        speed_b_kmh=292.0,
        accel_a_g=0.5,
        accel_b_g=0.3,
        decel_delta_g=0.2,
        throttle_a=100.0,
        throttle_b=100.0,
        brake_a=0.0,
        brake_b=0.0,
        brake_delta_pct=0.0,
        same_lap=True,
        is_normal_slipstream=True,
    )

    signals = detector.evaluate_frame(feat)
    assert len(signals) == 0, "Slipstream filter must suppress candidate triggers on straights"


def test_synchronized_braking_filtered_out():
    """Verify normal synchronized corner braking is rejected."""
    detector = MultiSignalDetector()
    feat = FrameFeatures(
        index=0,
        time_offset=10.0,
        timestamp="13:30:10.000",
        gap_meters=16.0,
        closing_speed_ms=3.0,
        speed_difference_kmh=10.0,
        speed_a_kmh=180.0,
        speed_b_kmh=170.0,
        accel_a_g=-3.5,
        accel_b_g=-3.3,
        decel_delta_g=0.2,
        throttle_a=0.0,
        throttle_b=0.0,
        brake_a=90.0,
        brake_b=85.0,
        brake_delta_pct=5.0,
        same_lap=True,
        is_synchronized_braking=True,
    )

    signals = detector.evaluate_frame(feat)
    assert len(signals) == 0, "Synchronized corner entry braking must not trigger candidate"


def test_temporal_segmentation_and_merging():
    """Verify proximate triggered frames are merged into a single coherent episode."""
    detector = MultiSignalDetector()
    segmenter = EpisodeSegmenter(
        SegmenterConfig(pre_trigger_padding_sec=2.0, post_trigger_padding_sec=2.0, merge_gap_seconds=3.0)
    )

    # Create a 20-frame sequence (0.0s to 1.9s at 0.1s step)
    # Triggers occur at 0.5s, 0.6s, 0.7s (cluster 1) and 1.2s, 1.3s (cluster 2 within 3s merge gap)
    frames: List[TelemetryPointSchema] = []
    for k in range(25):
        t = round(k * 0.1, 1)
        # Incident triggers between 0.5 and 1.3
        is_incident = (0.5 <= t <= 0.7) or (1.1 <= t <= 1.3)
        gap = 4.0 if is_incident else 30.0
        closing = 9.0 if is_incident else 0.0
        brake_a = 90.0 if is_incident else 0.0
        frames.append(make_frame(offset_sec=t, gap=gap, closing=closing, brake_a=brake_a))

    features = extract_pairwise_features(frames, dt_sec=0.1)
    triggered = detector.detect_candidate_frames(features)
    assert len(triggered) >= 4

    episodes = segmenter.segment_triggers(triggered, features, dt_sec=0.1)
    # The two clusters (0.5-0.7 and 1.1-1.3) have a gap of 0.4s (< 3.0s merge gap), so they must merge into 1 episode!
    assert len(episodes) == 1
    assert episodes[0].peak_time_offset in (0.5, 0.6, 0.7, 1.1, 1.2, 1.3)


def test_separate_events_remain_separate():
    """Verify interactions separated by more than merge_gap_seconds remain distinct episodes."""
    detector = MultiSignalDetector()
    segmenter = EpisodeSegmenter(
        SegmenterConfig(pre_trigger_padding_sec=1.0, post_trigger_padding_sec=1.0, merge_gap_seconds=2.0)
    )

    # Triggers at 1.0s and at 10.0s (9.0s gap > 2.0s merge gap)
    frames: List[TelemetryPointSchema] = []
    for k in range(120):
        t = round(k * 0.1, 1)
        is_ev1 = 1.0 <= t <= 1.2
        is_ev2 = 10.0 <= t <= 10.2
        is_inc = is_ev1 or is_ev2
        gap = 4.0 if is_inc else 30.0
        closing = 9.0 if is_inc else 0.0
        brake_a = 90.0 if is_inc else 0.0
        frames.append(make_frame(offset_sec=t, gap=gap, closing=closing, brake_a=brake_a))

    features = extract_pairwise_features(frames, dt_sec=0.1)
    triggered = detector.detect_candidate_frames(features)

    episodes = segmenter.segment_triggers(triggered, features, dt_sec=0.1)
    # Must produce exactly 2 distinct episodes!
    assert len(episodes) == 2


def test_candidate_evidence_scoring_and_dossier():
    """Verify neutral evidence strength calculation and dossier fields."""
    sig1 = EvidenceSignal(
        signal_type=EvidenceSignalType.SPATIAL_PROXIMITY,
        timestamp="13:30:15.000",
        time_offset=15.0,
        observed_value=3.2,
        threshold_value=5.0,
        unit="m",
        description="Critical proximity",
    )
    sig2 = EvidenceSignal(
        signal_type=EvidenceSignalType.KINEMATIC_CLOSING,
        timestamp="13:30:15.000",
        time_offset=15.0,
        observed_value=11.2,
        threshold_value=6.0,
        unit="m/s",
        description="High closing rate",
    )
    sig3 = EvidenceSignal(
        signal_type=EvidenceSignalType.VEHICLE_RESPONSE,
        timestamp="13:30:15.000",
        time_offset=15.0,
        observed_value=75.0,
        threshold_value=50.0,
        unit="%",
        description="Braking delta",
    )

    score = compute_evidence_strength(
        signals=[sig1, sig2, sig3],
        min_gap=3.2,
        peak_closing=11.2,
        max_decel_delta=2.8,
        has_rcm_match=True,
    )
    # Score must be bounded in [10, 100]
    assert 70 <= score <= 100
    assert classify_event_type(min_gap=3.2, peak_closing=11.2, max_decel_delta=2.8) == CandidateEventType.CONTACT_CANDIDATE


def test_evaluation_against_ground_truth_reference():
    """Verify evaluation metrics computation against official Monza reference cases."""
    from app.evidence.candidate import CandidateDossier

    # Mock candidate matching REF-MONZA-03 (MAG vs GAS, Lap 19)
    cand_mag_gas = CandidateDossier(
        candidate_id="CAND-TEST-MAG-GAS",
        session_id="f1-2024-monza-race",
        event_type=CandidateEventType.CONTACT_CANDIDATE,
        status=CandidateStatus.PENDING_REVIEW,
        event_start="13:30:10.000",
        event_peak="13:30:15.000",
        event_end="13:30:20.000",
        duration_seconds=10.0,
        driver_a="MAG",
        driver_b="GAS",
        lap_number_a=19,
        lap_number_b=19,
        same_lap=True,
        minimum_gap_meters=3.1,
        peak_closing_speed_ms=8.5,
        speed_delta_at_peak=22.0,
        speed_a_at_peak=160.0,
        speed_b_at_peak=138.0,
        evidence_strength=85,
    )

    metrics = evaluate_candidates_against_ground_truth(
        candidates=[cand_mag_gas],
        reference_cases=MONZA_2024_REFERENCE_CASES,
        session_telemetry_hours=1.4,
    )

    assert metrics.total_candidates_detected == 1
    assert metrics.true_positives == 1
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 2  # Other 2 reference cases not in this single mock test
    assert metrics.precision == 1.0
    assert round(metrics.recall, 2) == 0.33
