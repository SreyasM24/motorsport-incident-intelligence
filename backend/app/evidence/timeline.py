"""Chronological event timeline generator for incident candidate episodes.

Transforms continuous telemetry dynamics into an objective sequence of
descriptive milestones relative to the event peak (T=0.0s).
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.evidence.features import FrameFeatures


class TimelineMilestone(BaseModel):
    """Chronological marker within the incident candidate interaction episode."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    timestamp: str = Field(..., description="Wall-clock time string (HH:MM:SS.mmm)")
    relative_offset_sec: float = Field(..., description="Seconds relative to event peak (e.g. -2.5, 0.0, +1.8)")
    label: str = Field(..., description="Short milestone descriptor (e.g. 'T-2.0s: Approach Phase')")
    description: str = Field(..., description="Objective empirical observation without fault attribution")
    icon_type: str = Field(default="approach", description="approach, proximity, contact, motion, response, exit")
    evidence_ref: Optional[str] = None


def generate_event_timeline(
    features: List[FrameFeatures],
    peak_offset: float,
    driver_a: str,
    driver_b: str,
) -> List[TimelineMilestone]:
    """Generate a chronological sequence of empirical milestones from interaction features."""
    if not features:
        return []

    milestones: List[TimelineMilestone] = []

    # 1. Approach milestone (Earliest frame in window)
    first_feat = features[0]
    t_first = round(first_feat.time_offset - peak_offset, 2)
    milestones.append(
        TimelineMilestone(
            timestamp=first_feat.timestamp,
            relative_offset_sec=t_first,
            label=f"T{t_first:+.1f}s: Approach Phase",
            description=f"Cars {driver_a} and {driver_b} converge at {first_feat.gap_meters:.1f}m separation (speeds: {first_feat.speed_a_kmh:.0f} vs {first_feat.speed_b_kmh:.0f} km/h).",
            icon_type="approach",
            evidence_ref=f"APPROACH_{first_feat.timestamp}",
        )
    )

    # 2. Braking onset milestone (if braking occurs before peak)
    brake_frames = [f for f in features if f.time_offset < peak_offset and (f.brake_a > 20.0 or f.brake_b > 20.0)]
    if brake_frames:
        bf = brake_frames[0]
        t_brake = round(bf.time_offset - peak_offset, 2)
        milestones.append(
            TimelineMilestone(
                timestamp=bf.timestamp,
                relative_offset_sec=t_brake,
                label=f"T{t_brake:+.1f}s: Braking Onset",
                description=f"Initial deceleration initiated: {driver_a} brake={bf.brake_a:.0f}%, {driver_b} brake={bf.brake_b:.0f}%, closing rate={bf.closing_speed_ms:.1f} m/s.",
                icon_type="response",
                evidence_ref=f"BRAKING_{bf.timestamp}",
            )
        )

    # 3. Peak closing speed milestone (if distinct from peak proximity)
    peak_closing_feat = max(features, key=lambda f: abs(f.closing_speed_ms))
    t_closing = round(peak_closing_feat.time_offset - peak_offset, 2)
    if abs(t_closing) >= 0.2:
        milestones.append(
            TimelineMilestone(
                timestamp=peak_closing_feat.timestamp,
                relative_offset_sec=t_closing,
                label=f"T{t_closing:+.1f}s: Peak Closing Velocity",
                description=f"Maximum approach velocity observed: {peak_closing_feat.closing_speed_ms:.1f} m/s at {peak_closing_feat.gap_meters:.1f}m gap.",
                icon_type="motion",
                evidence_ref=f"CLOSING_{peak_closing_feat.timestamp}",
            )
        )

    # 4. Minimum proximity / Apex milestone (T=0.0s)
    peak_feat = min(features, key=lambda f: f.gap_meters)
    t_peak = round(peak_feat.time_offset - peak_offset, 2)
    is_critical = peak_feat.gap_meters <= 3.5
    milestones.append(
        TimelineMilestone(
            timestamp=peak_feat.timestamp,
            relative_offset_sec=t_peak,
            label=f"T{t_peak:+.1f}s: Minimum Proximity Apex",
            description=f"Closest spatial clearance reached: {peak_feat.gap_meters:.2f}m (speed delta: {peak_feat.speed_difference_kmh:.1f} km/h).",
            icon_type="contact" if is_critical else "proximity",
            evidence_ref=f"APEX_{peak_feat.timestamp}",
        )
    )

    # 5. Exit / Separation milestone (Last frame in window)
    last_feat = features[-1]
    t_last = round(last_feat.time_offset - peak_offset, 2)
    milestones.append(
        TimelineMilestone(
            timestamp=last_feat.timestamp,
            relative_offset_sec=t_last,
            label=f"T{t_last:+.1f}s: Separation & Corner Exit",
            description=f"Cars diverge; gap expands to {last_feat.gap_meters:.1f}m as drivers apply throttle ({driver_a}: {last_feat.throttle_a:.0f}%, {driver_b}: {last_feat.throttle_b:.0f}%).",
            icon_type="exit",
            evidence_ref=f"EXIT_{last_feat.timestamp}",
        )
    )

    # Sort milestones chronologically
    milestones.sort(key=lambda m: m.relative_offset_sec)
    return milestones
