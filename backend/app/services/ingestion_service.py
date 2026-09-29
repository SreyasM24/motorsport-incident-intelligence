"""Ingestion service coordinating FastF1 and OpenF1 data providers and optional persistence."""

from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session as DBSession

from app.core.logging import logger
from app.data.domain import (
    NormalizedRace,
    NormalizedSession,
    NormalizedDriver,
    NormalizedLap,
    NormalizedTelemetryPoint,
)
from app.data.fastf1.loader import FastF1DataSource
from app.data.openf1.client import OpenF1Client
from app.data.persistence import (
    persist_race,
    persist_session,
    persist_drivers,
    persist_telemetry_batch,
)
from app.models.race import Race
from app.models.session import Session as SessionModel
from app.models.driver import Driver


class IngestionService:
    """Service layer coordinating motorsport data ingestion, normalization, and persistence."""

    def __init__(
        self,
        fastf1_source: Optional[FastF1DataSource] = None,
        openf1_client: Optional[OpenF1Client] = None,
    ):
        self.fastf1 = fastf1_source or FastF1DataSource()
        self.openf1 = openf1_client or OpenF1Client()

    # -------------------------------------------------------------------------
    # Calendar & Event Operations
    # -------------------------------------------------------------------------

    def load_season_calendar(
        self,
        season: int,
        persist: bool = False,
        db: Optional[DBSession] = None,
    ) -> List[NormalizedRace]:
        """Fetch and normalize all events in a championship season."""
        races = self.fastf1.get_season_events(season)

        if persist and db is not None:
            for race_norm in races:
                try:
                    persist_race(db, race_norm)
                except Exception as e:
                    logger.warning(f"Failed to persist race {race_norm.id}: {e}")
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Commit failed after persisting season races: {e}")

        return races

    def load_event(
        self,
        season: int,
        round_or_name: Union[int, str],
        persist: bool = False,
        db: Optional[DBSession] = None,
    ) -> NormalizedRace:
        """Fetch and normalize a specific event by round number or name."""
        race = self.fastf1.get_event(season, round_or_name)
        if persist and db is not None:
            persist_race(db, race)
            db.commit()
        return race

    # -------------------------------------------------------------------------
    # Session Operations
    # -------------------------------------------------------------------------

    def load_session_metadata(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        persist: bool = False,
        db: Optional[DBSession] = None,
    ) -> NormalizedSession:
        """Fetch metadata for a specific session."""
        session = self.fastf1.get_session(season, round_or_name, session_identifier)
        if persist and db is not None:
            persist_session(db, session)
            db.commit()
        return session

    def load_session_drivers(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        persist: bool = False,
        db: Optional[DBSession] = None,
    ) -> List[NormalizedDriver]:
        """Fetch driver roster for a specific session."""
        drivers = self.fastf1.get_session_drivers(season, round_or_name, session_identifier)
        if persist and db is not None and drivers:
            session_id = drivers[0].session_id
            persist_drivers(db, session_id, drivers)
            db.commit()
        return drivers

    def load_session_laps(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        driver: Optional[str] = None,
    ) -> List[NormalizedLap]:
        """Fetch lap timing records for a session."""
        return self.fastf1.get_session_laps(
            season, round_or_name, session_identifier, driver=driver
        )

    # -------------------------------------------------------------------------
    # Telemetry Operations
    # -------------------------------------------------------------------------

    def load_driver_telemetry(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        driver: str,
        lap: Optional[int] = None,
        persist: bool = False,
        db: Optional[DBSession] = None,
    ) -> List[NormalizedTelemetryPoint]:
        """Fetch raw telemetry points for a specific driver and optional lap.

        Preserves raw multi-rate observation channels (no interpolation/resampling).
        """
        points = self.fastf1.get_driver_telemetry(
            season=season,
            round_or_name=round_or_name,
            session_identifier=session_identifier,
            driver=driver,
            lap=lap,
        )

        if persist and db is not None and points:
            session = self.fastf1.get_session(season, round_or_name, session_identifier)
            driver_obj = self.fastf1.get_session_drivers(season, round_or_name, session_identifier)
            driver_id = f"{session.id}-{driver.lower()}"
            persist_telemetry_batch(db, session.id, driver_id, points)
            db.commit()

        return points

    def load_all_driver_telemetry(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        lap: Optional[int] = None,
    ) -> Dict[str, List[NormalizedTelemetryPoint]]:
        """Fetch telemetry points for all participating drivers for a lap or session."""
        drivers = self.load_session_drivers(season, round_or_name, session_identifier)
        result: Dict[str, List[NormalizedTelemetryPoint]] = {}

        for drv in drivers:
            try:
                pts = self.load_driver_telemetry(
                    season=season,
                    round_or_name=round_or_name,
                    session_identifier=session_identifier,
                    driver=drv.code,
                    lap=lap,
                )
                result[drv.code] = pts
            except Exception as e:
                logger.warning(f"Could not load telemetry for driver {drv.code}: {e}")
                result[drv.code] = []

        return result

    # -------------------------------------------------------------------------
    # Full Session Database Sync
    # -------------------------------------------------------------------------

    def sync_session_to_database(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        db: DBSession,
    ) -> Tuple[Race, SessionModel, List[Driver]]:
        """Perform controlled synchronization of Race, Session, and Drivers into DB."""
        event_norm = self.load_event(season, round_or_name)
        session_norm = self.load_session_metadata(season, round_or_name, session_identifier)
        drivers_norm = self.load_session_drivers(season, round_or_name, session_identifier)

        race_db = persist_race(db, event_norm)
        session_db = persist_session(db, session_norm)
        drivers_db = persist_drivers(db, session_db.id, drivers_norm)

        db.commit()
        logger.info(
            f"Successfully synced session {session_db.id} with {len(drivers_db)} drivers"
        )
        return race_db, session_db, drivers_db


@lru_cache()
def get_ingestion_service() -> IngestionService:
    """Singleton provider for IngestionService."""
    return IngestionService()
