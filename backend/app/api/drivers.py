"""API router for drivers."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.connection import get_db
from app.models.driver import Driver
from app.schemas.driver import DriverResponse, DriverStats
from app.core.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", response_model=List[DriverResponse], summary="List all drivers")
def get_drivers(
    db: Session = Depends(get_db),
) -> List[DriverResponse]:
    """Retrieve all drivers across ingested sessions."""
    drivers = db.scalars(select(Driver).order_by(Driver.number.asc())).all()
    # Deduplicate by code
    seen_codes = set()
    unique_drivers = []
    for d in drivers:
        if d.code not in seen_codes:
            seen_codes.add(d.code)
            unique_drivers.append(d)

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
        for d in unique_drivers
    ]


@router.get("/{code}", response_model=DriverResponse, summary="Get driver profile")
def get_driver(
    code: str,
    db: Session = Depends(get_db),
) -> DriverResponse:
    """Retrieve single driver details by 3-letter driver code (e.g. VER, HAM)."""
    driver = db.scalar(select(Driver).where(Driver.code == code.upper()))
    if not driver:
        raise ResourceNotFoundException("Driver", code.upper())

    return DriverResponse(
        code=driver.code,
        number=driver.number,
        name=driver.full_name,
        team=driver.team,
        team_color=driver.team_color or "#E10600",
        secondary_color=driver.secondary_color,
        country=driver.nationality or "FIA",
        stats=DriverStats(
            laps_completed=driver.laps_completed,
            avg_speed_kmh=driver.avg_speed_kmh or 0.0,
            max_speed_kmh=driver.max_speed_kmh or 0.0,
            incidents_involved=len(driver.incident_participations),
            interactions_detected=0,
        ),
    )
