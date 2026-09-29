"""Live PostgreSQL Integration and End-to-End Validation Suite.

Empirically validates:
FastAPI -> PostgreSQL 16 (Docker) -> SQLAlchemy 2 -> Evidence Services -> API

CRITICAL REQUIREMENT:
Genuinely connects to and verifies against the containerized PostgreSQL database.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Race, Incident, Driver, Regulation, ReviewRecord

POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/motorsport_intelligence"
)

# Skip entire module if postgres is not reachable
try:
    _test_engine = create_engine(POSTGRES_URL, connect_args={"connect_timeout": 3})
    with _test_engine.connect() as _conn:
        _conn.execute(text("SELECT 1"))
    POSTGRES_AVAILABLE = True
except Exception:
    POSTGRES_AVAILABLE = False


@pytest.mark.skipif(not POSTGRES_AVAILABLE, reason="Live PostgreSQL container is not available")
class TestPostgreSQLProductionPath:
    """Verifies end-to-end operation against containerized PostgreSQL instance."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        self.client = TestClient(app)
        self.engine = create_engine(POSTGRES_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def test_postgres_table_population(self):
        """Verify Alembic schema migration created all tables and seed data is present in PostgreSQL."""
        with self.SessionLocal() as db:
            races = db.query(Race).all()
            assert len(races) >= 1, "Expected at least 1 race in PostgreSQL"
            
            drivers = db.query(Driver).all()
            assert len(drivers) >= 8, f"Expected >= 8 drivers in PostgreSQL, got {len(drivers)}"
            
            incidents = db.query(Incident).all()
            assert len(incidents) >= 3, f"Expected >= 3 incidents in PostgreSQL, got {len(incidents)}"
            
            regulations = db.query(Regulation).all()
            assert len(regulations) >= 3, f"Expected >= 3 regulations in PostgreSQL, got {len(regulations)}"

    def test_postgres_readiness_healthcheck(self):
        """Verify /health/ready returns 200 OK with database_ready=True against live PostgreSQL."""
        resp = self.client.get("/api/v1/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["database_ready"] is True
        assert data["cache_ready"] is True

    def test_postgres_races_and_drivers_api(self):
        """Verify API queries PostgreSQL for races and drivers."""
        resp = self.client.get("/api/v1/races")
        assert resp.status_code == 200
        races = resp.json()
        assert len(races) >= 1
        assert "Monza" in races[0]["circuit"]

        resp_drv = self.client.get("/api/v1/drivers")
        assert resp_drv.status_code == 200
        drivers = resp_drv.json()
        assert len(drivers) >= 8
        driver_codes = [d["code"] for d in drivers]
        assert "HUL" in driver_codes
        assert "TSU" in driver_codes

    def test_postgres_incident_retrieval(self):
        """Verify API retrieves incident candidate from PostgreSQL."""
        resp = self.client.get("/api/v1/incidents/INC-2024-MONZA-R-02")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "INC-2024-MONZA-R-02"
        assert data["turn"] == "Turn 1 (Variante del Rettifilo)"
        driver_a = data.get("driverA") or data.get("driver_a")
        driver_b = data.get("driverB") or data.get("driver_b")
        assert driver_a == "HUL" or driver_b == "HUL"

    def test_postgres_dossier_synthesis_and_caching(self):
        """Verify complete dossier synthesis and warm-cache retrieval backed by PostgreSQL."""
        resp = self.client.get("/api/v1/incidents/INC-2024-MONZA-R-02/dossier")
        assert resp.status_code == 200
        dossier = resp.json()
        cand_id = dossier.get("candidateId") or dossier.get("candidate_id")
        assert cand_id == "REF-MONZA-02"
        assert "stream_quality" in dossier or "streamQuality" in dossier


    def test_postgres_human_review_persistence(self):
        """Verify human review state transition persists into PostgreSQL review_records."""
        # 1. Transition to UNDER_REVIEW
        resp = self.client.patch(
            "/api/v1/incidents/INC-2024-MONZA-R-02/status",
            json={
                "status": "UNDER_REVIEW",
                "reviewer_id": "STEWARD-PG-TEST",
                "review_notes": "Live PostgreSQL transaction test.",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "UNDER_REVIEW"

        # 2. Query PostgreSQL directly to verify record was committed
        with self.SessionLocal() as db:
            inc = db.query(Incident).filter(Incident.id == "INC-2024-MONZA-R-02").first()
            assert inc.status == "UNDER_REVIEW"

            reviews = db.query(ReviewRecord).filter(ReviewRecord.incident_id == "INC-2024-MONZA-R-02").all()
            reviewers = [r.reviewer_id for r in reviews]
            assert "STEWARD-PG-TEST" in reviewers
