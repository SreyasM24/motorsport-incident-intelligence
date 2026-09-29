"""Candidate event dossier builder.

Synthesizes segmented episodes, extracted features, and contextual signals
into a neutral, comprehensive CandidateDossier.
"""

from typing import Any, Dict, List, Optional
import numpy as np

from app.evidence.candidate import (
    CandidateDossier,
    CandidateEventType,
    CandidateStatus,
    DataQualityFlags,
    EvidenceSignal,
)
from app.evidence.segmenter import SegmentedEpisode
from app.schemas.telemetry import TelemetryPointSchema


def compute_evidence_strength(
    signals: List[EvidenceSignal],
    min_gap: float,
    peak_closing: float,
    max_decel_delta: float,
    has_rcm_match: bool,
) -> int:
    """Calculate neutral empirical evidence strength (0-100).

    DOCTRINE:
        This metric strictly denotes the degree of sensor convergence and signal diversity.
        It NEVER represents guilt, fault, penalty, or steward confidence.
    """
    unique_types = {s.signal_type for s in signals}
    # Base score by signal diversity
    base_score = min(70, len(unique_types) * 20)

    # Proximity depth bonus
    proximity_bonus = 0
    if min_gap <= 3.5:
        proximity_bonus = 20
    elif min_gap <= 6.0:
        proximity_bonus = 10
    elif min_gap <= 10.0:
        proximity_bonus = 5

    # Kinematic intensity bonus
    closing_bonus = 5 if abs(peak_closing) >= 8.0 else 0
    decel_bonus = 5 if max_decel_delta >= 2.5 else 0

    # Race control correlation bonus
    rcm_bonus = 10 if has_rcm_match else 0

    total = base_score + proximity_bonus + closing_bonus + decel_bonus + rcm_bonus
    return int(np.clip(total, 10, 100))


def classify_event_type(
    min_gap: float,
    peak_closing: float,
    max_decel_delta: float,
) -> CandidateEventType:
    """Assign neutral physical classification based on empirical dominance."""
    # F1 cars are 2.0m wide; center-to-center distance < 3.5m indicates potential wheel overlap
    if min_gap <= 3.5:
        return CandidateEventType.CONTACT_CANDIDATE
    if abs(peak_closing) >= 10.0:
        return CandidateEventType.RAPID_PROXIMITY_EVENT
    if max_decel_delta >= 2.5:
        return CandidateEventType.SUDDEN_DECELERATION_EVENT
    return CandidateEventType.MULTI_SIGNAL_INTERACTION


def build_candidate_dossier(
    candidate_id: str,
    session_id: str,
    episode: SegmentedEpisode,
    driver_a: str,
    driver_b: str,
    raw_frames: List[TelemetryPointSchema],
    race_control_messages: Optional[List[Dict[str, Any]]] = None,
) -> CandidateDossier:
    """Construct a full CandidateDossier from a segmented interaction episode."""
    # Extract peak frame
    peak_feat = min(episode.encompassing_features, key=lambda f: f.gap_meters)

    min_gap = round(float(peak_feat.gap_meters), 2)
    peak_closing = round(
        float(max(episode.encompassing_features, key=lambda f: abs(f.closing_speed_ms)).closing_speed_ms), 2
    )
    max_decel_delta = round(
        float(max(episode.encompassing_features, key=lambda f: f.decel_delta_g).decel_delta_g), 2
    )

    # Collect unique signals across all triggered frames in the episode
    signal_map: Dict[str, EvidenceSignal] = {}
    for tf in episode.triggered_frames:
        for sig in tf.signals:
            key = f"{sig.signal_type}_{sig.timestamp}"
            signal_map[key] = sig
    all_signals = list(signal_map.values())

    # Check for race control match
    has_rcm_match = any(m.get("driver_match") for m in (race_control_messages or []))

    evidence_score = compute_evidence_strength(
        all_signals,
        min_gap=min_gap,
        peak_closing=peak_closing,
        max_decel_delta=max_decel_delta,
        has_rcm_match=has_rcm_match,
    )

    event_type = classify_event_type(min_gap, peak_closing, max_decel_delta)

    # Lap numbers
    lap_a = peak_feat.distance_a
    lap_b = peak_feat.distance_b

    # Spatial coordinates from raw frames if available
    peak_raw = raw_frames[peak_feat.index] if peak_feat.index < len(raw_frames) else None

    # Vehicle responses
    braking_change = {
        "brake_a_pct": peak_feat.brake_a,
        "brake_b_pct": peak_feat.brake_b,
        "brake_delta_pct": peak_feat.brake_delta_pct,
        "accel_a_g": peak_feat.accel_a_g,
        "accel_b_g": peak_feat.accel_b_g,
        "decel_delta_g": peak_feat.decel_delta_g,
    }
    throttle_change = {
        "throttle_a_pct": peak_feat.throttle_a,
        "throttle_b_pct": peak_feat.throttle_b,
    }
    trajectory_change = {
        "speed_difference_kmh": peak_feat.speed_difference_kmh,
        "peak_closing_speed_ms": peak_closing,
    }

    # Data Quality Flags
    has_different_laps = not peak_feat.same_lap
    missing_tel = any(f.speed_a == 0.0 and f.speed_b == 0.0 for f in raw_frames[episode.start_index : episode.end_index + 1])
    low_cov = episode.duration_seconds < 1.0

    dq_flags = DataQualityFlags(
        missing_telemetry=missing_tel,
        interpolation_heavy=False,
        coordinate_discontinuity=False,
        different_laps=has_different_laps,
        incomplete_driver_data=False,
        race_control_unavailable=(race_control_messages is None),
        low_temporal_coverage=low_cov,
        quality_summary="NOMINAL" if not (missing_tel or has_different_laps) else "LIMITED_FIDELITY",
    )

    summary = (
        f"Multi-signal interaction candidate between {driver_a} and {driver_b}: "
        f"minimum proximity {min_gap}m at {episode.peak_timestamp} "
        f"(closing rate {peak_closing} m/s, decel delta {max_decel_delta}G, "
        f"speed delta {peak_feat.speed_difference_kmh} km/h). "
        f"Signals observed: {len(all_signals)}. Status: Requires Human Review."
    )

    return CandidateDossier(
        candidate_id=candidate_id,
        session_id=session_id,
        event_type=event_type,
        status=CandidateStatus.PENDING_REVIEW,
        event_start=episode.start_timestamp,
        event_peak=episode.peak_timestamp,
        event_end=episode.end_timestamp,
        duration_seconds=episode.duration_seconds,
        driver_a=driver_a,
        driver_b=driver_b,
        lap_number_a=peak_raw.lap_number_a if peak_raw else None,
        lap_number_b=peak_raw.lap_number_b if peak_raw else None,
        same_lap=peak_feat.same_lap,
        track_distance_a=peak_raw.distance_a if peak_raw else None,
        track_distance_b=peak_raw.distance_b if peak_raw else None,
        minimum_gap_meters=min_gap,
        peak_closing_speed_ms=peak_closing,
        speed_delta_at_peak=peak_feat.speed_difference_kmh,
        speed_a_at_peak=peak_feat.speed_a_kmh,
        speed_b_at_peak=peak_feat.speed_b_kmh,
        braking_change=braking_change,
        throttle_change=throttle_change,
        trajectory_change=trajectory_change,
        race_control_context=race_control_messages or [],
        evidence_signals=all_signals,
        evidence_strength=evidence_score,
        data_quality_flags=dq_flags,
        preprocessing_version="telemetry_preprocessing_v1",
        detection_method="MULTI_SIGNAL_RECONSTRUCTION_V1",
        summary=summary,
    )
