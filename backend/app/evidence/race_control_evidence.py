"""Race control evidence representation and message correlation.

Structures official steward bulletins, flag statuses, and investigations
as contextual supporting evidence without asserting automated culpability.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class RaceControlMessageEvidence(BaseModel):
    """An individual race control notice correlated with the candidate event window."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    timestamp: str = Field(..., description="Wall-clock timestamp string from steward feed")
    relative_time_to_peak_sec: Optional[float] = Field(
        default=None, description="Seconds relative to candidate peak (e.g. +14.2s for investigation notice)"
    )
    category: str = Field(..., description="Flag, CarEvent, TrackStatus, SafetyCar, Investigation")
    flag: Optional[str] = None
    message: str = Field(..., description="Raw verbatim message from FIA race control terminal")
    scope: Optional[str] = None
    sector: Optional[int] = None
    lap: Optional[int] = None
    driver_match: bool = Field(default=False, description="True if message explicitly names participating drivers")


class RaceControlEvidenceSummary(BaseModel):
    """Synthesized race control context for an incident evidence dossier."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    active_flags: List[str] = Field(default_factory=list, description="Flags active during event window (YELLOW, VSC, etc.)")
    correlated_messages: List[RaceControlMessageEvidence] = Field(default_factory=list)
    race_control_context_strength: int = Field(
        default=0, ge=0, le=100, description="Contextual alignment strength score (0-100)"
    )
    steward_note: str = Field(
        default="Race control messages reflect official steward room activity and flag status. "
        "They provide supporting contextual evidence and do not constitute automated guilt determination."
    )


def build_race_control_evidence(
    raw_messages: List[Dict[str, Any]],
    peak_timestamp_str: str,
    driver_a: str,
    driver_b: str,
) -> RaceControlEvidenceSummary:
    """Filter, correlate, and score race control messages against the candidate event."""
    correlated: List[RaceControlMessageEvidence] = []
    active_flags: List[str] = []

    def parse_sec(ts_str: str) -> Optional[float]:
        try:
            # Handle timestamps like "2024-09-01 13:30:30" or "13:30:30.123"
            time_part = ts_str.split(" ")[-1]
            parts = time_part.split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        except Exception:
            return None

    peak_sec = parse_sec(peak_timestamp_str)
    has_direct_driver_match = False

    for msg in raw_messages:
        ts = str(msg.get("timestamp", ""))
        category = str(msg.get("category", "Other"))
        flag = msg.get("flag")
        text = str(msg.get("message", ""))

        msg_sec = parse_sec(ts)
        rel_sec = round(msg_sec - peak_sec, 1) if (msg_sec is not None and peak_sec is not None) else None

        # Filter messages within reasonable incident horizon: [-30s before peak, +180s after peak]
        in_window = True
        if rel_sec is not None:
            in_window = -30.0 <= rel_sec <= 180.0

        if not in_window:
            continue

        drv_match = msg.get("driver_match", False)
        if drv_match:
            has_direct_driver_match = True

        if flag and flag not in active_flags:
            active_flags.append(flag)

        correlated.append(
            RaceControlMessageEvidence(
                timestamp=ts,
                relative_time_to_peak_sec=rel_sec,
                category=category,
                flag=flag,
                message=text,
                scope=msg.get("scope"),
                sector=msg.get("sector"),
                lap=msg.get("lap"),
                driver_match=drv_match,
            )
        )

    # Score context strength
    context_score = 0
    if has_direct_driver_match:
        context_score = 90
    elif active_flags:
        context_score = 50
    elif correlated:
        context_score = 25

    return RaceControlEvidenceSummary(
        active_flags=active_flags,
        correlated_messages=correlated,
        race_control_context_strength=context_score,
    )
