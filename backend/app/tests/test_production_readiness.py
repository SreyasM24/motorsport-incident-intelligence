"""Production readiness, security hardening, and reliability test suite.

Validates:
1. Defense-in-depth security headers (nosniff, SAMEORIGIN, XSS, Referrer, Permissions).
2. Liveness, readiness, and degraded health probe behavior.
3. In-memory sliding-window rate limiting & 429 response structure.
4. Internal server error sanitation (traceback & secret leakage suppression).
5. Database backup, restore, and table integrity verification.
6. OpenAPI contract schema completeness and CORS headers.
7. Anti-adjudication guardrails (no autonomous penalty/fault assignment).
"""

import gzip
import os
import sqlite3
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scripts.db_backup_restore import (
    create_backup,
    restore_backup,
    verify_database_integrity,
)
from app.core.middleware import SecurityHeadersMiddleware, RateLimiterMiddleware
from app.core.exceptions import register_exception_handlers


def test_security_headers_present_on_all_responses(client: TestClient):
    """Verify defense-in-depth security headers are present on API responses."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200

    headers = resp.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers.get("Permissions-Policy", "")

    # Request tracing headers
    assert "X-Request-ID" in headers
    assert len(headers["X-Request-ID"]) > 0
    assert "X-Response-Time-Ms" in headers


def test_health_and_readiness_probes(client: TestClient):
    """Verify liveness and readiness probe status contracts."""
    # Liveness probe
    live_resp = client.get("/api/v1/health/live")
    assert live_resp.status_code == 200
    live_data = live_resp.json()
    assert live_data["status"] == "alive"
    assert "timestamp" in live_data

    # Readiness probe
    ready_resp = client.get("/api/v1/health/ready")
    assert ready_resp.status_code in (200, 503)
    ready_data = ready_resp.json()
    assert "database_ready" in ready_data
    assert "cache_ready" in ready_data
    assert ready_data["status"] in ("ready", "not_ready")


def test_readiness_probe_degraded_on_db_disconnect(client: TestClient, monkeypatch):
    """Verify readiness probe returns 503 when database is unavailable."""
    monkeypatch.setattr(
        "app.api.health.check_db_connection",
        lambda: (False, "Database connection refused"),
    )

    resp = client.get("/api/v1/health/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "not_ready"
    assert data["database_ready"] is False
    assert "refused" in data["details"]["database_message"].lower()


def test_rate_limiter_never_throttles_health_probes():
    """Verify health and readiness probes are completely exempt from rate limiting."""
    test_app = FastAPI()
    test_app.add_middleware(RateLimiterMiddleware, max_requests_per_window=3, window_seconds=60)

    @test_app.get("/api/v1/health/live")
    async def live():
        return {"status": "alive"}

    @test_app.get("/api/v1/health/ready")
    async def ready():
        return {"status": "ready"}

    client = TestClient(test_app)
    # Send 10 rapid requests, far exceeding limit of 3
    for _ in range(10):
        resp_live = client.get("/api/v1/health/live")
        assert resp_live.status_code == 200

        resp_ready = client.get("/api/v1/health/ready")
        assert resp_ready.status_code == 200


def test_rate_limiter_throttles_excessive_traffic():
    """Verify sliding-window rate limiter returns 429 with Retry-After header."""
    test_app = FastAPI()
    test_app.add_middleware(RateLimiterMiddleware, max_requests_per_window=3, window_seconds=60)

    @test_app.get("/api/v1/analysis/expensive")
    async def expensive():
        return {"status": "done"}

    client = TestClient(test_app)
    # First 3 allowed
    for _ in range(3):
        resp = client.get("/api/v1/analysis/expensive")
        assert resp.status_code == 200

    # 4th request must be throttled
    resp = client.get("/api/v1/analysis/expensive")
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
    data = resp.json()
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "retry_after_seconds" in data["error"]["details"]


def test_internal_server_error_sanitization():
    """Verify unhandled exceptions suppress internal tracebacks and secret leakage."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/trigger-crash")
    async def trigger_crash():
        raise RuntimeError("CRITICAL_INTERNAL_DB_PASSWORD_LEAK=secret123")

    client = TestClient(test_app, raise_server_exceptions=False)
    resp = client.get("/trigger-crash")
    assert resp.status_code == 500
    data = resp.json()

    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["error"]["message"] == "An unexpected server error occurred. Please consult system logs."
    # Crucially ensure raw message / secrets are NOT returned in JSON
    assert "CRITICAL_INTERNAL_DB_PASSWORD_LEAK" not in resp.text
    assert "secret123" not in resp.text
    assert "Traceback" not in resp.text


def test_database_backup_and_restore_roundtrip(tmp_path):
    """Verify database backup creation, restore, and table integrity verification."""
    db_file = tmp_path / "test_production.db"
    db_url = f"sqlite:///{db_file}"

    # 1. Initialize SQLite database with sample tables and rows
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE incident_candidates (id TEXT PRIMARY KEY, title TEXT, status TEXT)")
    cur.execute("CREATE TABLE evidence_items (id TEXT PRIMARY KEY, candidate_id TEXT, modality TEXT)")
    cur.execute("INSERT INTO incident_candidates VALUES ('CAND-01', 'Turn 1 Clash', 'PENDING_REVIEW')")
    cur.execute("INSERT INTO incident_candidates VALUES ('CAND-02', 'Pit Exit Infringement', 'UNDER_INVESTIGATION')")
    cur.execute("INSERT INTO evidence_items VALUES ('EVD-01', 'CAND-01', 'TELEMETRY')")
    conn.commit()
    conn.close()

    # 2. Verify initial integrity
    initial_stats = verify_database_integrity(db_url)
    assert initial_stats["is_operational"] is True
    assert "incident_candidates" in initial_stats["tables"]
    assert initial_stats["row_counts"]["incident_candidates"] == 2
    assert initial_stats["row_counts"]["evidence_items"] == 1

    # 3. Create backup
    backup_file = str(tmp_path / "backup_snapshot.db.gz")
    out_path = create_backup(db_url=db_url, output_file=backup_file, output_dir=str(tmp_path))
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0

    # 4. Corrupt / truncate database
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("DELETE FROM incident_candidates")
    conn.commit()
    conn.close()

    corrupted_stats = verify_database_integrity(db_url)
    assert corrupted_stats["row_counts"]["incident_candidates"] == 0

    # 5. Restore from backup
    restored_db_file = tmp_path / "restored_production.db"
    restored_url = f"sqlite:///{restored_db_file}"
    success = restore_backup(backup_file=out_path, db_url=restored_url)
    assert success is True

    # 6. Verify restored database matches original
    restored_stats = verify_database_integrity(restored_url)
    assert restored_stats["is_operational"] is True
    assert restored_stats["row_counts"]["incident_candidates"] == 2
    assert restored_stats["row_counts"]["evidence_items"] == 1


def test_api_contract_and_openapi_completeness(client: TestClient):
    """Verify OpenAPI 3.x schema defines all required investigation and review endpoints."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()

    assert spec.get("openapi", "").startswith("3.")
    paths = spec.get("paths", {})

    # Core required endpoints
    expected_endpoints = [
        "/api/v1/health",
        "/api/v1/health/live",
        "/api/v1/health/ready",
        "/api/v1/cases/{candidate_id}/workspace",
        "/api/v1/cases/{candidate_id}/questions",
        "/api/v1/cases/{candidate_id}/timeline",
        "/api/v1/assistant/query",
        "/api/v1/analysis/candidates/persist",
        "/api/v1/incidents",
        "/api/v1/races",
    ]

    for endpoint in expected_endpoints:
        assert endpoint in paths, f"Missing expected endpoint in OpenAPI schema: {endpoint}"


def test_cors_preflight_headers(client: TestClient):
    """Verify CORS preflight headers accept configured origins and methods."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    resp = client.options("/api/v1/cases", headers=headers)
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers


def test_steward_guardrails_prevent_automated_penalties(client: TestClient):
    """Verify that case and evidence responses do not include automated fault or penalty attributes."""
    resp = client.get("/openapi.json")
    spec = resp.json()
    schemas = spec.get("components", {}).get("schemas", {})

    # Verify no schema promotes automated fault or penalty determination
    forbidden_terms = ["penalty_recommendation", "guilty_driver", "fault_verdict", "automated_ruling"]
    for schema_name, schema_def in schemas.items():
        properties = schema_def.get("properties", {})
        for prop in properties:
            for term in forbidden_terms:
                assert term not in prop.lower(), f"Forbidden automated adjudication field found: {prop} in {schema_name}"
