"""Unit tests for the health diagnostics endpoint."""

def test_health_endpoint(client):
    """Verify health endpoint responds with structured integration diagnostic payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["app_name"] == "Motorsport Incident Intelligence API"
    assert data["app_version"] == "1.0.0"
    assert data["api_prefix"] == "/api/v1"
    assert "database_connected" in data
    assert isinstance(data["database_connected"], bool)
    assert "fastf1_cache_ready" in data
    assert isinstance(data["fastf1_cache_ready"], bool)
    assert "fastf1_cache_dir" in data
    assert "timestamp" in data
