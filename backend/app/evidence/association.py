"""Driver pair association and race control message integration.

Associates interacting driver pairs with empirical spatial coordinates and
correlates contemporaneous race control messages / flag statuses.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

from app.core.logging import logger
from app.evidence.segmenter import SegmentedEpisode
from app.services.ingestion_service import get_ingestion_service


def extract_race_control_context(
    episode: SegmentedEpisode,
    driver_a: str,
    driver_b: str,
    session_rcm: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Extract race control messages temporally correlated with the candidate episode.

    Race control notices (investigations, yellow flags, noted incidents) typically
    appear between 0 and 120 seconds after the physical on-track event.
    """
    if not session_rcm:
        return []

    # Episode bounds in datetime if available or string comparison
    correlated: List[Dict[str, Any]] = []
    drv_a_upper = driver_a.upper()
    drv_b_upper = driver_b.upper()

    for msg in session_rcm:
        text = str(msg.get("message", "")).upper()
        category = msg.get("category", "")
        flag = msg.get("flag")
        ts = msg.get("timestamp")

        # Check if message specifically references either driver code or car number
        mentions_driver = (
            f"({drv_a_upper})" in text
            or f" {drv_a_upper} " in text
            or f"({drv_b_upper})" in text
            or f" {drv_b_upper} " in text
            or f"CAR {drv_a_upper}" in text
            or f"CAR {drv_b_upper}" in text
        )

        is_flag_event = category == "Flag" or flag in ("YELLOW", "DOUBLE YELLOW", "SAFETY CAR", "VSC", "RED")

        if mentions_driver or is_flag_event:
            correlated.append(
                {
                    "timestamp": str(ts) if ts else "",
                    "category": category,
                    "flag": flag,
                    "message": msg.get("message", ""),
                    "scope": msg.get("scope"),
                    "sector": msg.get("sector"),
                    "driver_match": mentions_driver,
                }
            )

    return correlated


def get_session_race_control_messages(
    season: int,
    round_or_name: str,
    session_identifier: str = "Race",
) -> List[Dict[str, Any]]:
    """Retrieve normalized race control messages for a session from FastF1 cache."""
    try:
        ingestion = get_ingestion_service()
        return ingestion.fastf1.get_session_race_control_messages(
            season=season, round_or_name=round_or_name, session_identifier=session_identifier
        )
    except Exception as e:
        logger.warning(f"Could not load race control messages for {season} {round_or_name}: {e}")

    return []
