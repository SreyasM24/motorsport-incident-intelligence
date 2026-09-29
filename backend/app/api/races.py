"""API router for championship races."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.connection import get_db
from app.models.race import Race
from app.schemas.race import RaceResponse, RaceSessionSchema
from app.core.exceptions import ResourceNotFoundException

from app.services.ingestion_service import get_ingestion_service
from app.core.logging import logger

router = APIRouter(prefix="/races", tags=["Races"])


@router.get("", response_model=List[RaceResponse], summary="List championship races")
def get_races(
    season: Optional[str] = Query(default=None, description="Filter by championship season, e.g. 2024"),
    auto_fetch: bool = Query(default=False, description="Fetch from FastF1 if database has no records"),
    db: Session = Depends(get_db),
) -> List[RaceResponse]:
    """Retrieve all ingested championship races. If auto_fetch=True and DB is unseeded, loads from FastF1."""
    stmt = select(Race)
    target_season = season or "2024"
    if season:
        stmt = stmt.where(Race.season == season)
    stmt = stmt.order_by(Race.round.asc().nulls_last())

    races = db.scalars(stmt).all()
    if not races and auto_fetch:
        # Fallback to IngestionService with real FastF1 schedule
        try:
            ingestion = get_ingestion_service()
            norm_races = ingestion.load_season_calendar(int(target_season), persist=True, db=db)
            return [
                RaceResponse(
                    id=r.id,
                    name=r.name,
                    circuit=r.circuit_name,
                    country=r.country,
                    season=r.season,
                    round=r.round_number,
                    year=int(r.season) if r.season.isdigit() else 2024,
                    session_type="Race",
                    date=str(r.event_date) if r.event_date else "",
                    drivers_count=20,
                    candidates_count=0,
                    confirmed_count=0,
                    review_count=0,
                    status="ANALYSIS READY",
                    telemetry_available=True,
                    video_available=False,
                    regulation_set=f"FIA Sporting Regulations {r.season}",
                    sessions=[],
                )
                for r in norm_races
            ]
        except Exception as e:
            logger.warning(f"Could not load live season calendar via FastF1: {e}")

    results: List[RaceResponse] = []
    for r in races:
        sessions_schemas = [
            RaceSessionSchema(
                name=s.name,
                laps=s.total_laps,
                status=s.status.replace("_", " "),
            )
            for s in r.sessions
        ]
        results.append(
            RaceResponse(
                id=r.id,
                name=r.name,
                circuit=r.circuit,
                country=r.country,
                season=r.season,
                round=r.round,
                year=int(r.season) if r.season.isdigit() else 2024,
                session_type="Race",
                date=str(r.date) if r.date else "",
                drivers_count=20,
                candidates_count=0,
                confirmed_count=0,
                review_count=0,
                status="ANALYSIS READY",
                telemetry_available=True,
                video_available=False,
                regulation_set=f"FIA Sporting Regulations {r.season}",
                sessions=sessions_schemas,
            )
        )
    return results


@router.get("/{race_id}", response_model=RaceResponse, summary="Get race details")
def get_race(
    race_id: str,
    db: Session = Depends(get_db),
) -> RaceResponse:
    """Retrieve single race details by unique race ID."""
    race = db.get(Race, race_id)
    if not race:
        raise ResourceNotFoundException("Race", race_id)

    sessions_schemas = [
        RaceSessionSchema(
            name=s.name,
            laps=s.total_laps,
            status=s.status.replace("_", " "),
        )
        for s in race.sessions
    ]

    return RaceResponse(
        id=race.id,
        name=race.name,
        circuit=race.circuit,
        country=race.country,
        season=race.season,
        round=race.round,
        year=int(race.season) if race.season.isdigit() else 2024,
        session_type="Race",
        date=str(race.date) if race.date else "",
        drivers_count=20,
        candidates_count=0,
        confirmed_count=0,
        review_count=0,
        status="ANALYSIS READY",
        telemetry_available=True,
        video_available=False,
        regulation_set=f"FIA Sporting Regulations {race.season}",
        sessions=sessions_schemas,
    )
