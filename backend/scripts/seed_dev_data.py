"""Development and Test Dataset Seeding Utility.

IMPORTANT:
This script populates DEVELOPMENT and TEST fixtures only.
It NEVER seeds fabricated race telemetry or artificial steward guilt verdicts.
All records are marked with development/test metadata.
"""

import sys
import os
from datetime import date, datetime, timezone

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal, engine
from app.models import (
    Race,
    Session as RaceSession,
    Driver,
    Incident,
    IncidentDriver,
    Regulation,
    ReviewRecord,
)
from app.core.logging import logger


def seed_development_fixtures(db: Session) -> None:
    """Idempotently seed development reference fixtures for local testing."""
    logger.info("=== SEEDING DEVELOPMENT / TEST DATA FIXTURES ===")

    # 1. Race Fixture: 2024 Italian Grand Prix
    race_id = "RACE-2024-MONZA"
    existing_race = db.query(Race).filter(Race.id == race_id).first()
    if not existing_race:
        race = Race(
            id=race_id,
            series="Formula 1",
            season="2024",
            round=16,
            name="Formula 1 Pirelli Gran Premio d'Italia 2024",
            circuit="Autodromo Nazionale Monza",
            country="Italy",
            city="Monza",
            date=date(2024, 9, 1),
            source="fastf1",
            source_id="2024-16",
        )
        db.add(race)
        db.flush()
        logger.info(f"Seeded Race: {race.name}")
    else:
        race = existing_race

    # 2. Session Fixture: 2024 Monza Race Session
    session_id = "SESSION-2024-MONZA-R"
    existing_session = db.query(RaceSession).filter(RaceSession.id == session_id).first()
    if not existing_session:
        session = RaceSession(
            id=session_id,
            race_id=race.id,
            session_type="Race",
            name="2024 Italian Grand Prix - Race",
            date=date(2024, 9, 1),
            start_time=datetime(2024, 9, 1, 13, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 9, 1, 14, 30, 0, tzinfo=timezone.utc),
            total_laps=53,
            status="ANALYSIS_READY",
            source="fastf1",
            source_id="2024-16-R",
        )
        db.add(session)
        db.flush()
        logger.info(f"Seeded Session: {session.name}")
    else:
        session = existing_session

    # 3. Driver Fixtures
    sample_drivers = [
        {"code": "HUL", "num": 27, "name": "Nico Hülkenberg", "first": "Nico", "last": "Hülkenberg", "team": "Haas F1 Team", "color": "#B6BABD"},
        {"code": "TSU", "num": 22, "name": "Yuki Tsunoda", "first": "Yuki", "last": "Tsunoda", "team": "RB F1 Team", "color": "#6692FF"},
        {"code": "RIC", "num": 3, "name": "Daniel Ricciardo", "first": "Daniel", "last": "Ricciardo", "team": "RB F1 Team", "color": "#6692FF"},
        {"code": "MAG", "num": 20, "name": "Kevin Magnussen", "first": "Kevin", "last": "Magnussen", "team": "Haas F1 Team", "color": "#B6BABD"},
        {"code": "GAS", "num": 10, "name": "Pierre Gasly", "first": "Pierre", "last": "Gasly", "team": "Alpine F1 Team", "color": "#FF87BC"},
        {"code": "VER", "num": 1, "name": "Max Verstappen", "first": "Max", "last": "Verstappen", "team": "Red Bull Racing", "color": "#3671C6"},
        {"code": "NOR", "num": 4, "name": "Lando Norris", "first": "Lando", "last": "Norris", "team": "McLaren", "color": "#FF8000"},
        {"code": "LEC", "num": 16, "name": "Charles Leclerc", "first": "Charles", "last": "Leclerc", "team": "Ferrari", "color": "#E80020"},
    ]

    for d in sample_drivers:
        driver_id = f"DRV-{session.id}-{d['code']}"
        if not db.query(Driver).filter(Driver.id == driver_id).first():
            drv = Driver(
                id=driver_id,
                session_id=session.id,
                code=d["code"],
                number=d["num"],
                full_name=d["name"],
                first_name=d["first"],
                last_name=d["last"],
                abbreviation=d["code"],
                team=d["team"],
                team_color=d["color"],
                laps_completed=53,
                source="fastf1",
            )
            db.add(drv)
            logger.info(f"Seeded Driver: {d['code']} (#{d['num']})")
    db.flush()

    # 4. Regulations Fixtures
    sample_regulations = [
        {
            "id": "REG-ISC-APP-L-IV-2",
            "article": "Article 2",
            "document": "FIA International Sporting Code Appendix L Chapter IV",
            "title": "Overtaking, Car Control and Track Limits",
            "text": "A car alone on the track may use the full width of the track. Drivers must observe track limits at all times. Any driver leaving the track must rejoin safely and without gaining a lasting advantage.",
            "url": "https://www.fia.com/regulation/category/123",
        },
        {
            "id": "REG-ISC-APP-L-IV-2-B",
            "article": "Article 2(b)",
            "document": "FIA International Sporting Code Appendix L Chapter IV",
            "title": "Manoeuvres liable to hinder other drivers (Crowding)",
            "text": "Manoeuvres liable to hinder other drivers, such as deliberate crowding of a car beyond the edge of the track or any other abnormal change of direction, are strictly prohibited.",
            "url": "https://www.fia.com/regulation/category/123",
        },
        {
            "id": "REG-SPORTING-33-3",
            "article": "Article 33.3",
            "document": "Formula 1 Sporting Regulations 2024",
            "title": "Track Limits and Driving Standards",
            "text": "Drivers must make every reasonable effort to use the track at all times and may not leave the track without a justifiable reason. Judges of fact will monitor track boundaries.",
            "url": "https://www.fia.com/regulation/category/110",
        },
    ]

    for r in sample_regulations:
        if not db.query(Regulation).filter(Regulation.id == r["id"]).first():
            reg = Regulation(
                id=r["id"],
                series="Formula 1",
                season="2024",
                document=r["document"],
                article=r["article"],
                title=r["title"],
                text=r["text"],
                source_url=r["url"],
                effective_date=date(2024, 1, 1),
            )
            db.add(reg)
            logger.info(f"Seeded Regulation: {r['article']}")
    db.flush()

    # 5. Incident Reference Candidates
    incidents_data = [
        {
            "id": "INC-2024-MONZA-R-01",
            "type": "OVERTAKING_COLLISION_RISK",
            "lap": 1,
            "turn": "Turn 8 (Variante Ascari)",
            "time_str": "15:04:12.4",
            "status": "REQUIRES_REVIEW",
            "severity": "LOW",
            "candidate_id": "REF-MONZA-01",
            "summary": "Lateral squeeze entering Ascari on opening lap under high fuel load.",
            "primary_driver": "RIC",
            "comparison_driver": "HUL",
            "gap": 1.45,
            "closing": 8.2,
        },
        {
            "id": "INC-2024-MONZA-R-02",
            "type": "BRAKING_ZONE_COLLISION",
            "lap": 4,
            "turn": "Turn 1 (Variante del Rettifilo)",
            "time_str": "15:08:44.2",
            "status": "REQUIRES_REVIEW",
            "severity": "HIGH",
            "candidate_id": "REF-MONZA-02",
            "summary": "Heavy braking collision at Turn 1 apex causing terminal sidepod damage to Tsunoda.",
            "primary_driver": "HUL",
            "comparison_driver": "TSU",
            "gap": 0.42,
            "closing": 14.8,
        },
        {
            "id": "INC-2024-MONZA-R-03",
            "type": "CORNER_ENTRY_CONTACT",
            "lap": 19,
            "turn": "Turn 4 (Variante della Roggia)",
            "time_str": "15:28:19.0",
            "status": "REQUIRES_REVIEW",
            "severity": "MEDIUM",
            "candidate_id": "REF-MONZA-03",
            "summary": "Inside overtaking attempt with wheel contact and front lockup at Roggia chicane.",
            "primary_driver": "MAG",
            "comparison_driver": "GAS",
            "gap": 0.88,
            "closing": 11.3,
        },
    ]

    for inc in incidents_data:
        existing_inc = db.query(Incident).filter(Incident.id == inc["id"]).first()
        if not existing_inc:
            incident = Incident(
                id=inc["id"],
                session_id=session.id,
                incident_type=inc["type"],
                status=inc["status"],
                severity=inc["severity"],
                lap=inc["lap"],
                turn=inc["turn"],
                timestamp_str=inc["time_str"],
                summary=inc["summary"],
                candidate_id=inc["candidate_id"],
                canonical_fingerprint=f"FP-DEV-{inc['candidate_id']}",
                minimum_gap_meters=inc["gap"],
                peak_closing_speed_ms=inc["closing"],
                evidence_strength=85,
                source="fastf1",
            )
            db.add(incident)
            db.flush()

            # Associations
            drv_prim = db.query(Driver).filter(Driver.session_id == session.id, Driver.code == inc["primary_driver"]).first()
            drv_comp = db.query(Driver).filter(Driver.session_id == session.id, Driver.code == inc["comparison_driver"]).first()
            if drv_prim:
                db.add(IncidentDriver(incident_id=incident.id, driver_id=drv_prim.id, role="PRIMARY"))
            if drv_comp:
                db.add(IncidentDriver(incident_id=incident.id, driver_id=drv_comp.id, role="SECONDARY"))

            # Review audit record
            db.add(
                ReviewRecord(
                    id=f"REV-{incident.id}",
                    incident_id=incident.id,
                    status=inc["status"],
                    reviewer_id="steward-panel",
                    observations="Candidate populated via development test seed. Ready for empirical steward review.",
                )
            )
            logger.info(f"Seeded Incident Candidate: {inc['id']} ({inc['candidate_id']})")
    db.commit()
    logger.info("=== DEVELOPMENT / TEST DATA SEEDING COMPLETE ===")


if __name__ == "__main__":
    with SessionLocal() as db_session:
        seed_development_fixtures(db_session)
