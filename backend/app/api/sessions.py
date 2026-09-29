"""API router for sessions and session overview analytics."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select, func
from app.database.connection import get_db
from app.models.session import Session
from app.models.driver import Driver
from app.models.incident import Incident
from app.models.incident_driver import IncidentDriver
from app.schemas.session import SessionResponse, SessionSummaryResponse, RaceActivityPoint
from app.schemas.driver import DriverResponse, DriverStats
from app.schemas.incident import IncidentSummary
from app.core.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/{session_id}", response_model=SessionResponse, summary="Get session metadata")
def get_session(
    session_id: str,
    db: DBSession = Depends(get_db),
) -> SessionResponse:
    """Retrieve session by unique identifier."""
    session = db.get(Session, session_id)
    if not session:
        raise ResourceNotFoundException("Session", session_id)

    return SessionResponse(
        id=session.id,
        race_id=session.race_id,
        session_type=session.session_type,
        name=session.name,
        date=str(session.date) if session.date else None,
        start_time=session.start_time.isoformat() if session.start_time else None,
        end_time=session.end_time.isoformat() if session.end_time else None,
        total_laps=session.total_laps,
        status=session.status,
    )


@router.get("/{session_id}/summary", response_model=SessionSummaryResponse, summary="Get session headline metrics")
def get_session_summary(
    session_id: str,
    db: DBSession = Depends(get_db),
) -> SessionSummaryResponse:
    """Return aggregated metric cards for the Session Dashboard."""
    session = db.get(Session, session_id)
    if not session:
        raise ResourceNotFoundException("Session", session_id)

    drivers_count = db.scalar(
        select(func.count(Driver.id)).where(Driver.session_id == session_id)
    ) or 0

    candidates_count = db.scalar(
        select(func.count(Incident.id)).where(Incident.session_id == session_id)
    ) or 0

    requires_review = db.scalar(
        select(func.count(Incident.id)).where(
            Incident.session_id == session_id,
            Incident.status == "REQUIRES_REVIEW",
        )
    ) or 0

    reviewed_count = db.scalar(
        select(func.count(Incident.id)).where(
            Incident.session_id == session_id,
            Incident.status == "REVIEWED",
        )
    ) or 0

    race_name = session.race.name if session.race else "Grand Prix"
    circuit = session.race.circuit if session.race else "Circuit"

    return SessionSummaryResponse(
        session_id=session.id,
        race_name=race_name,
        circuit=circuit,
        drivers_count=drivers_count,
        candidates_count=candidates_count,
        requires_review_count=requires_review,
        reviewed_count=reviewed_count,
        telemetry_status="CONNECTED",
        incident_analysis_status="AVAILABLE",
        regulations_status="CONNECTED",
        video_status="AVAILABLE",
        ai_analysis_status="AVAILABLE",
    )


@router.get("/{session_id}/activity", response_model=List[RaceActivityPoint], summary="Get session incident activity by lap")
def get_session_activity(
    session_id: str,
    db: DBSession = Depends(get_db),
) -> List[RaceActivityPoint]:
    """Return lap-by-lap interaction density for Recharts visualization."""
    session = db.get(Session, session_id)
    if not session:
        raise ResourceNotFoundException("Session", session_id)

    stmt = (
        select(
            Incident.lap,
            func.count(Incident.id).label("candidates"),
            func.sum(func.cast(Incident.severity.in_(["HIGH", "CRITICAL"]), func.integer)).label("abnormal"),
            func.sum(func.cast(Incident.evidence_strength >= 80, func.integer)).label("high_conf"),
        )
        .where(Incident.session_id == session_id)
        .group_by(Incident.lap)
        .order_by(Incident.lap.asc())
    )

    rows = db.execute(stmt).all()
    if not rows:
        return []

    return [
        RaceActivityPoint(
            lap=r.lap,
            candidates=int(r.candidates or 0),
            abnormal=int(r.abnormal or 0),
            high_confidence=int(r.high_conf or 0),
        )
        for r in rows
    ]


from app.services.ingestion_service import get_ingestion_service
from app.core.logging import logger


@router.get("/{session_id}/drivers", response_model=List[DriverResponse], summary="List drivers in session")
def get_session_drivers(
    session_id: str,
    db: DBSession = Depends(get_db),
) -> List[DriverResponse]:
    """Retrieve all driver transponders calibrated for this session."""
    session = db.get(Session, session_id)
    if not session:
        raise ResourceNotFoundException("Session", session_id)

    drivers = db.scalars(
        select(Driver).where(Driver.session_id == session_id).order_by(Driver.number.asc())
    ).all()

    if not drivers and session.race:
        try:
            ingestion = get_ingestion_service()
            norm_drivers = ingestion.load_session_drivers(
                season=int(session.race.season),
                round_or_name=session.race.round or session.race.name,
                session_identifier=session.session_type,
                persist=True,
                db=db,
            )
            return [
                DriverResponse(
                    code=d.code,
                    number=d.number,
                    name=d.full_name,
                    team=d.team,
                    team_color=d.team_color or "#E10600",
                    secondary_color=d.secondary_color,
                    country=d.nationality or "FIA",
                    stats=DriverStats(
                        laps_completed=d.laps_completed,
                        avg_speed_kmh=d.avg_speed_kmh or 0.0,
                        max_speed_kmh=d.max_speed_kmh or 0.0,
                        incidents_involved=0,
                        interactions_detected=0,
                    ),
                )
                for d in norm_drivers
            ]
        except Exception as e:
            logger.warning(f"Could not load live session drivers: {e}")

    return [
        DriverResponse(
            code=d.code,
            number=d.number,
            name=d.full_name,
            team=d.team,
            team_color=d.team_color or "#E10600",
            secondary_color=d.secondary_color,
            country=d.nationality or "FIA",
            stats=DriverStats(
                laps_completed=d.laps_completed,
                avg_speed_kmh=d.avg_speed_kmh or 0.0,
                max_speed_kmh=d.max_speed_kmh or 0.0,
                incidents_involved=len(d.incident_participations),
                interactions_detected=0,
            ),
        )
        for d in drivers
    ]
