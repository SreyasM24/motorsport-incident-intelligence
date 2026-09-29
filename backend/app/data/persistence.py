"""Controlled database persistence layer for normalized motorsport metadata and bounded telemetry."""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select

from app.core.logging import logger
from app.models.race import Race
from app.models.session import Session as SessionModel
from app.models.driver import Driver
from app.models.telemetry import Telemetry
from app.data.domain import (
    NormalizedRace,
    NormalizedSession,
    NormalizedDriver,
    NormalizedTelemetryPoint,
)


def persist_race(db: DBSession, norm_race: NormalizedRace) -> Race:
    """Idempotently persist or update a Grand Prix event in the database."""
    existing = db.execute(select(Race).where(Race.id == norm_race.id)).scalar_one_or_none()
    if existing:
        existing.name = norm_race.name
        existing.circuit = norm_race.circuit_name
        existing.country = norm_race.country
        existing.city = norm_race.city
        existing.date = norm_race.event_date
        existing.round = norm_race.round_number
        existing.source = norm_race.source
        existing.source_id = norm_race.source_id
        db.flush()
        return existing

    race = Race(
        id=norm_race.id,
        series=norm_race.series,
        season=norm_race.season,
        round=norm_race.round_number,
        name=norm_race.name,
        circuit=norm_race.circuit_name,
        country=norm_race.country,
        city=norm_race.city,
        date=norm_race.event_date,
        source=norm_race.source,
        source_id=norm_race.source_id,
    )
    db.add(race)
    db.flush()
    logger.debug(f"Persisted race metadata: {race.id}")
    return race


def persist_session(db: DBSession, norm_session: NormalizedSession) -> SessionModel:
    """Idempotently persist or update a race session in the database."""
    existing = db.execute(
        select(SessionModel).where(SessionModel.id == norm_session.id)
    ).scalar_one_or_none()

    if existing:
        existing.session_type = norm_session.session_type
        existing.name = norm_session.session_name
        existing.date = norm_session.session_date
        existing.start_time = norm_session.start_time
        existing.end_time = norm_session.end_time
        existing.total_laps = norm_session.total_laps
        existing.status = norm_session.status
        existing.source = norm_session.source
        existing.source_id = norm_session.source_id
        db.flush()
        return existing

    sess = SessionModel(
        id=norm_session.id,
        race_id=norm_session.race_id,
        session_type=norm_session.session_type,
        name=norm_session.session_name,
        date=norm_session.session_date,
        start_time=norm_session.start_time,
        end_time=norm_session.end_time,
        total_laps=norm_session.total_laps,
        status=norm_session.status,
        source=norm_session.source,
        source_id=norm_session.source_id,
    )
    db.add(sess)
    db.flush()
    logger.debug(f"Persisted session metadata: {sess.id}")
    return sess


def persist_drivers(
    db: DBSession, session_id: str, drivers: List[NormalizedDriver]
) -> List[Driver]:
    """Idempotently persist or update driver roster for a session."""
    persisted: List[Driver] = []

    for d in drivers:
        existing = db.execute(
            select(Driver).where(Driver.session_id == session_id, Driver.code == d.code)
        ).scalar_one_or_none()

        if existing:
            existing.full_name = d.full_name
            existing.team = d.team
            existing.team_color = d.team_color
            existing.number = d.number
            existing.laps_completed = d.laps_completed
            existing.avg_speed_kmh = d.avg_speed_kmh
            existing.max_speed_kmh = d.max_speed_kmh
            existing.source = d.source
            existing.source_id = d.source_id
            persisted.append(existing)
        else:
            driver = Driver(
                id=d.id,
                session_id=session_id,
                code=d.code,
                number=d.number,
                full_name=d.full_name,
                first_name=d.first_name,
                last_name=d.last_name,
                abbreviation=d.abbreviation,
                nationality=d.nationality,
                team=d.team,
                team_color=d.team_color,
                secondary_color=d.secondary_color,
                laps_completed=d.laps_completed,
                avg_speed_kmh=d.avg_speed_kmh,
                max_speed_kmh=d.max_speed_kmh,
                source=d.source,
                source_id=d.source_id,
            )
            db.add(driver)
            persisted.append(driver)

    db.flush()
    logger.debug(f"Persisted {len(persisted)} drivers for session {session_id}")
    return persisted


def persist_telemetry_batch(
    db: DBSession,
    session_id: str,
    driver_id: str,
    points: List[NormalizedTelemetryPoint],
    batch_size: int = 1000,
) -> int:
    """Controlled persistence for bounded telemetry points in chunks.

    Only invoked for bounded, specific telemetry queries/slices to avoid
    dumping entire season multi-gigabyte data into relational tables prematurely.
    """
    if not points:
        return 0

    total_inserted = 0
    records = []

    for pt in points:
        record = Telemetry(
            session_id=session_id,
            driver_id=driver_id,
            timestamp=pt.timestamp,
            time_offset=pt.time_offset,
            lap_number=pt.lap_number,
            distance=pt.distance,
            x=pt.x,
            y=pt.y,
            z=pt.z,
            speed=pt.speed,
            throttle=pt.throttle,
            brake=pt.brake,
            steering=pt.steering,
            gear=pt.gear,
            rpm=pt.rpm,
            drs=pt.drs,
            accel_x=pt.accel_x,
            accel_y=pt.accel_y,
            source=pt.source,
        )
        records.append(record)

        if len(records) >= batch_size:
            db.bulk_save_objects(records)
            db.flush()
            total_inserted += len(records)
            records = []

    if records:
        db.bulk_save_objects(records)
        db.flush()
        total_inserted += len(records)

    logger.info(f"Persisted bounded telemetry batch: {total_inserted} points")
    return total_inserted
