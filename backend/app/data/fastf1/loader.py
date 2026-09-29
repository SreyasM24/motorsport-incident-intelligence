"""FastF1 data loader implementing the BaseDataSource interface.

Provides normalized access to F1 calendar, session metadata, driver rosters, lap records,
and bounded raw telemetry.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
from fastf1.core import Session as FastF1Session

from app.core.logging import logger
from app.data.base import BaseDataSource
from app.data.domain import (
    NormalizedRace,
    NormalizedSession,
    NormalizedDriver,
    NormalizedLap,
    NormalizedTelemetryPoint,
)
from app.data.fastf1.client import FastF1Client
from app.data.fastf1.normalizer import (
    normalize_fastf1_event,
    normalize_fastf1_session,
    normalize_fastf1_driver,
    normalize_fastf1_lap,
    normalize_fastf1_telemetry,
)
from app.data.fastf1.exceptions import (
    FastF1Error,
    FastF1SessionNotFoundError,
    FastF1DataUnavailableError,
)


class FastF1DataSource(BaseDataSource):
    """Data source adapter for official FastF1 timing and telemetry feeds."""

    def __init__(self, client: Optional[FastF1Client] = None, cache_dir: Optional[str] = None):
        self.client = client or FastF1Client(cache_dir=cache_dir)
        self._loaded_sessions: Dict[str, FastF1Session] = {}
        self._session_load_status: Dict[str, Dict[str, bool]] = {}

    @property
    def source_name(self) -> str:
        return "fastf1"

    def get_season_events(self, season: int) -> List[NormalizedRace]:
        """Load and normalize all championship events for a season."""
        schedule_df = self.client.get_event_schedule(season)
        races: List[NormalizedRace] = []

        for _, row in schedule_df.iterrows():
            # Exclude pre-season testing unless explicitly desired
            event_format = str(row.get("EventFormat", ""))
            if "testing" in event_format.lower():
                continue
            round_num = row.get("RoundNumber")
            if round_num is not None and not pd.isna(round_num) and int(round_num) == 0:
                continue

            try:
                norm_race = normalize_fastf1_event(row, season)
                races.append(norm_race)
            except Exception as e:
                logger.warning(f"Error normalizing FastF1 event row: {e}")
                continue

        return races

    def get_event(self, season: int, round_or_name: Union[int, str]) -> NormalizedRace:
        """Load and normalize a specific championship event."""
        event_series = self.client.get_event(season, round_or_name)
        return normalize_fastf1_event(event_series, season)

    def _ensure_session_loaded(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        laps: bool = True,
        telemetry: bool = False,
        weather: bool = False,
        messages: bool = False,
    ) -> FastF1Session:
        """Internal helper to load and cache a FastF1 session."""
        key = f"{season}_{round_or_name}_{session_identifier}"
        session = self._loaded_sessions.get(key)

        if session is None:
            session = self.client.get_session(season, round_or_name, session_identifier)
            self._loaded_sessions[key] = session

        status = self._session_load_status.get(key, {"laps": False, "telemetry": False, "messages": False})
        needs_laps = laps and not status.get("laps", False)
        needs_tel = telemetry and not status.get("telemetry", False)
        needs_msg = messages and not status.get("messages", False)

        if needs_laps or needs_tel or needs_msg:
            try:
                load_laps = laps or status.get("laps", False)
                load_telemetry = telemetry or status.get("telemetry", False)
                load_messages = messages or status.get("messages", False)
                logger.info(
                    f"FastF1: Loading data for {key} (laps={load_laps}, telemetry={load_telemetry}, messages={load_messages})"
                )
                session.load(
                    laps=load_laps,
                    telemetry=load_telemetry,
                    weather=weather,
                    messages=load_messages,
                )
                self._session_load_status[key] = {
                    "laps": load_laps,
                    "telemetry": load_telemetry,
                    "messages": load_messages,
                }
            except Exception as e:
                logger.warning(f"FastF1: Partial load failure for {key}: {e}")

        return session

    def get_session(
        self, season: int, round_or_name: Union[int, str], session_identifier: str
    ) -> NormalizedSession:
        """Retrieve metadata for a specific session."""
        event = self.get_event(season, round_or_name)
        session = self._ensure_session_loaded(
            season, round_or_name, session_identifier, laps=False, telemetry=False
        )
        return normalize_fastf1_session(session, season, event.id)

    def get_session_drivers(
        self, season: int, round_or_name: Union[int, str], session_identifier: str
    ) -> List[NormalizedDriver]:
        """Retrieve driver roster for a session."""
        event = self.get_event(season, round_or_name)
        session = self._ensure_session_loaded(
            season, round_or_name, session_identifier, laps=True, telemetry=False
        )
        norm_session = normalize_fastf1_session(session, season, event.id)

        drivers: List[NormalizedDriver] = []

        if hasattr(session, "results") and session.results is not None and not session.results.empty:
            for _, row in session.results.iterrows():
                try:
                    norm_driver = normalize_fastf1_driver(
                        row, session_id=norm_session.id, laps_df=session.laps
                    )
                    drivers.append(norm_driver)
                except Exception as e:
                    logger.warning(f"Error normalizing driver row: {e}")
                    continue
        elif hasattr(session, "drivers") and session.drivers:
            # Fallback if results table is not populated
            for drv_num in session.drivers:
                try:
                    drv_info = session.get_driver(drv_num)
                    norm_driver = normalize_fastf1_driver(
                        drv_info, session_id=norm_session.id, laps_df=session.laps
                    )
                    drivers.append(norm_driver)
                except Exception as e:
                    logger.warning(f"Error extracting driver {drv_num}: {e}")
                    continue

        return drivers

    def get_session_laps(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        driver: Optional[str] = None,
    ) -> List[NormalizedLap]:
        """Retrieve lap timing records for a session."""
        session = self._ensure_session_loaded(
            season, round_or_name, session_identifier, laps=True, telemetry=False
        )
        if session.laps is None or session.laps.empty:
            return []

        laps_df = session.laps
        if driver:
            # Filter by driver abbreviation or number
            laps_df = laps_df[
                (laps_df["Driver"] == str(driver).upper())
                | (laps_df["DriverNumber"] == str(driver))
            ]

        laps: List[NormalizedLap] = []
        for _, row in laps_df.iterrows():
            drv_code = str(row.get("Driver", ""))
            try:
                drv_num = int(row.get("DriverNumber", 0))
            except (ValueError, TypeError):
                drv_num = 0

            norm_lap = normalize_fastf1_lap(row, driver_code=drv_code, driver_number=drv_num)
            laps.append(norm_lap)

        return laps

    def get_driver_telemetry(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        driver: str,
        lap: Optional[int] = None,
    ) -> List[NormalizedTelemetryPoint]:
        """Retrieve raw telemetry data points for a specific driver and optional lap."""
        session = self._ensure_session_loaded(
            season, round_or_name, session_identifier, laps=True, telemetry=True
        )

        if session.laps is None or session.laps.empty:
            raise FastF1DataUnavailableError(
                message=f"No lap data available to locate driver '{driver}' telemetry",
                details={"driver": driver, "session": session_identifier},
            )

        driver_upper = str(driver).upper()
        driver_laps = session.laps.pick_drivers(driver_upper)
        if driver_laps.empty:
            # Try driver number
            driver_laps = session.laps[session.laps["DriverNumber"] == str(driver)]

        if driver_laps.empty:
            raise FastF1DataUnavailableError(
                message=f"Driver '{driver}' not found in session laps",
                details={"driver": driver},
            )

        # Get driver number for normalization
        driver_num = None
        try:
            driver_num = int(driver_laps.iloc[0]["DriverNumber"])
        except Exception:
            pass

        if lap is not None:
            lap_obj = driver_laps[driver_laps["LapNumber"] == lap]
            if lap_obj.empty:
                raise FastF1DataUnavailableError(
                    message=f"Lap {lap} not found for driver '{driver}'",
                    details={"driver": driver, "lap": lap},
                )
            tel_df = lap_obj.iloc[0].get_telemetry()
            return normalize_fastf1_telemetry(
                tel_df, driver_code=driver_upper, driver_number=driver_num, lap_number=lap
            )
        else:
            # Entire session driver telemetry (can be large, but preserves raw multi-rate stream)
            tel_df = driver_laps.get_telemetry()
            return normalize_fastf1_telemetry(
                tel_df, driver_code=driver_upper, driver_number=driver_num, lap_number=None
            )

    def get_session_race_control_messages(
        self, season: int, round_or_name: Union[int, str], session_identifier: str
    ) -> List[Dict[str, Any]]:
        """Retrieve race control messages for a session."""
        session = self._ensure_session_loaded(
            season, round_or_name, session_identifier, laps=False, telemetry=False, messages=True
        )
        if hasattr(session, "race_control_messages") and session.race_control_messages is not None:
            rcm_df = session.race_control_messages
            records: List[Dict[str, Any]] = []
            for _, row in rcm_df.iterrows():
                records.append(
                    {
                        "timestamp": str(row.get("Time")),
                        "category": row.get("Category"),
                        "message": str(row.get("Message", "")),
                        "status": row.get("Status"),
                        "flag": row.get("Flag"),
                        "scope": row.get("Scope"),
                        "sector": row.get("Sector"),
                        "lap": row.get("Lap"),
                    }
                )
            return records
        return []
