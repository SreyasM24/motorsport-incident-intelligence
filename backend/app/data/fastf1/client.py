"""Low-level FastF1 client wrapper with error handling and cache management."""

from typing import Any, Optional, Union
import pandas as pd
import fastf1
from fastf1.core import Session as FastF1Session

from app.core.logging import logger
from app.data.fastf1.cache import setup_fastf1_cache
from app.data.fastf1.exceptions import (
    FastF1Error,
    FastF1SessionNotFoundError,
    FastF1DataUnavailableError,
)


class FastF1Client:
    """Client for directly interfacing with the official FastF1 library."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize client and ensure FastF1 cache is configured."""
        self.cache_dir = setup_fastf1_cache(custom_dir=cache_dir)
        self._cache_enabled = True

    def get_event_schedule(self, season: int) -> pd.DataFrame:
        """Fetch the official race calendar for a season.

        Args:
            season: Championship year, e.g. 2024.

        Returns:
            DataFrame containing the event schedule.
        """
        try:
            logger.info(f"FastF1: Fetching event schedule for season {season}")
            schedule = fastf1.get_event_schedule(season)
            if schedule.empty:
                raise FastF1DataUnavailableError(
                    message=f"No event schedule available for season {season}",
                    details={"season": season},
                )
            return schedule
        except FastF1DataUnavailableError:
            raise
        except Exception as e:
            logger.error(f"FastF1: Error retrieving schedule for {season}: {e}")
            raise FastF1Error(
                message=f"Failed to retrieve season {season} schedule: {e}",
                details={"season": season},
            ) from e

    def get_event(self, season: int, round_or_name: Union[int, str]) -> pd.Series:
        """Fetch a specific event by round number or Grand Prix name.

        Args:
            season: Championship year, e.g. 2024.
            round_or_name: Round number (e.g. 16) or event name (e.g. 'Monza', 'Italian Grand Prix').

        Returns:
            Series representing the event.
        """
        try:
            logger.info(f"FastF1: Fetching event '{round_or_name}' for season {season}")
            event = fastf1.get_event(season, round_or_name)
            if event is None or (isinstance(event, pd.Series) and event.empty):
                raise FastF1SessionNotFoundError(season=season, event=str(round_or_name), session="N/A")
            return event
        except FastF1SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"FastF1: Error retrieving event '{round_or_name}' for {season}: {e}")
            raise FastF1Error(
                message=f"Failed to retrieve event '{round_or_name}' for {season}: {e}",
                details={"season": season, "event": str(round_or_name)},
            ) from e

    def get_session(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
    ) -> FastF1Session:
        """Fetch a raw FastF1 Session object.

        Args:
            season: Championship year, e.g. 2024.
            round_or_name: Round number or event name.
            session_identifier: 'Practice 1', 'Practice 2', 'Practice 3', 'Qualifying', 'Sprint', 'Race' (or 'R', 'Q', 'FP1', etc.).

        Returns:
            FastF1 Session instance.
        """
        try:
            logger.info(
                f"FastF1: Getting session: {season} - {round_or_name} - {session_identifier}"
            )
            session = fastf1.get_session(season, round_or_name, session_identifier)
            return session
        except Exception as e:
            logger.error(
                f"FastF1: Error fetching session {season} '{round_or_name}' '{session_identifier}': {e}"
            )
            raise FastF1SessionNotFoundError(
                season=season,
                event=str(round_or_name),
                session=str(session_identifier),
            ) from e
