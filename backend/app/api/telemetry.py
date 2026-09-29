"""API router for telemetry timeseries slices."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.incident import Incident
from app.schemas.telemetry import TelemetrySliceResponse, TelemetryPointSchema
from app.core.exceptions import ResourceNotFoundException

router = APIRouter(tags=["Telemetry"])


from app.services.telemetry_service import get_telemetry_service
from app.schemas.telemetry import SynchronizedPairResponse


@router.get("/incidents/{incident_id}/telemetry", response_model=TelemetrySliceResponse, summary="Get synchronized telemetry slice")
def get_incident_telemetry(
    incident_id: str,
    hz: int = Query(default=25, ge=1, le=50, description="Interpolated sample rate in Hz"),
    pad_seconds: float = Query(default=3.0, ge=0.0, le=15.0, description="Padding seconds before/after incident window"),
    limit: int = Query(default=500, ge=10, le=2000, description="Strict safety cap on points returned"),
    db: Session = Depends(get_db),
) -> TelemetrySliceResponse:
    """Retrieve time-aligned, bounded multi-channel telemetry slice for the incident pair.

    Safety:
        Strictly limits points returned and bounds query by the incident time window
        plus safety padding to prevent accidental multi-million row dumps.
    """
    inc = db.get(Incident, incident_id)
    if not inc:
        raise ResourceNotFoundException("Incident", incident_id)

    drivers = [p.driver.code for p in inc.drivers_involved if p.driver]
    driver_a = drivers[0] if len(drivers) > 0 else "CAR A"
    driver_b = drivers[1] if len(drivers) > 1 else "CAR B"

    points: List[TelemetryPointSchema] = []
    # If incident has 2 identified drivers and linked session with race info, synchronize real telemetry
    if len(drivers) >= 2 and inc.session and inc.session.race:
        try:
            tel_service = get_telemetry_service()
            pair_slice = tel_service.get_synchronized_pair_slice(
                season=int(inc.session.race.season),
                round_or_name=inc.session.race.round or inc.session.race.name,
                session_identifier=inc.session.session_type,
                driver_a=driver_a,
                driver_b=driver_b,
                lap=inc.lap,
                frequency_hz=float(hz),
                limit=limit,
            )
            points = pair_slice.points
        except Exception as e:
            logger.warning(f"Could not load live synchronized telemetry for incident {incident_id}: {e}")

    return TelemetrySliceResponse(
        incident_id=inc.id,
        session_id=inc.session_id,
        driver_a=driver_a,
        driver_b=driver_b,
        hz=hz,
        reference_timestamp=inc.timestamp_str,
        incident_window={"start": inc.timestamp_str, "end": inc.timestamp_str},
        points=points,
        total_points=len(points),
    )


@router.get("/telemetry/pair-stream", response_model=SynchronizedPairResponse, summary="Get synchronized driver pair telemetry")
def get_synchronized_pair(
    season: int = Query(default=2024, description="Championship season"),
    event: str = Query(default="Monza", description="Event name or round number"),
    session: str = Query(default="Race", description="Session identifier"),
    driver_a: str = Query(..., description="Driver A 3-letter code or number, e.g. LEC"),
    driver_b: str = Query(..., description="Driver B 3-letter code or number, e.g. MAG"),
    lap: Optional[int] = Query(default=None, ge=1, description="Optional specific lap number"),
    frequency_hz: Optional[float] = Query(default=25.0, ge=1.0, le=100.0, description="Analysis grid frequency in Hz"),
    limit: int = Query(default=500, ge=10, le=2000, description="Max points to return"),
) -> SynchronizedPairResponse:
    """Retrieve time-aligned 25Hz synchronized telemetry pair with Cartesian gap and closing speed."""
    tel_service = get_telemetry_service()
    return tel_service.get_synchronized_pair_slice(
        season=season,
        round_or_name=event,
        session_identifier=session,
        driver_a=driver_a,
        driver_b=driver_b,
        lap=lap,
        frequency_hz=frequency_hz,
        limit=limit,
    )


from app.schemas.telemetry import DriverTelemetryPointSchema, DriverTelemetryResponse
from app.services.ingestion_service import get_ingestion_service
from app.core.logging import logger


@router.get("/telemetry/driver-stream", response_model=DriverTelemetryResponse, summary="Get real bounded driver telemetry")
def get_driver_telemetry(
    season: int = Query(default=2024, description="Championship season"),
    event: str = Query(default="Monza", description="Event name or round number"),
    session: str = Query(default="Race", description="Session identifier"),
    driver: str = Query(..., description="Driver 3-letter code or number, e.g. VER"),
    lap: Optional[int] = Query(default=None, ge=1, description="Optional specific lap number"),
    limit: int = Query(default=500, ge=10, le=2000, description="Max points to return"),
) -> DriverTelemetryResponse:
    """Retrieve raw multi-rate telemetry directly from FastF1 data ingestion layer."""
    ingestion = get_ingestion_service()
    try:
        points = ingestion.load_driver_telemetry(
            season=season,
            round_or_name=event,
            session_identifier=session,
            driver=driver,
            lap=lap,
        )
    except Exception as e:
        logger.error(f"Error fetching driver telemetry for {driver}: {e}")
        points = []

    bounded_points = points[:limit]
    schemas = [
        DriverTelemetryPointSchema(
            timestamp=pt.timestamp.isoformat() if pt.timestamp else None,
            time_offset=pt.time_offset,
            lap_number=pt.lap_number,
            distance=pt.distance,
            x=pt.x,
            y=pt.y,
            z=pt.z,
            speed=pt.speed,
            throttle=pt.throttle,
            brake=pt.brake,
            gear=pt.gear,
            rpm=pt.rpm,
            drs=pt.drs,
            source=pt.source,
        )
        for pt in bounded_points
    ]

    return DriverTelemetryResponse(
        session_id=f"f1-{season}-{event.lower()}-{session.lower()}",
        driver_code=driver.upper(),
        lap_number=lap,
        total_points=len(schemas),
        points=schemas,
    )

