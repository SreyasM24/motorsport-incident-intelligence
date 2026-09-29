"""Unit tests for FastAPI core application initialization and routing."""

def test_root_endpoint(client):
    """Verify that root service discovery endpoint returns 200 and valid links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Motorsport Incident Intelligence API"
    assert data["status"] == "operational"
    assert "docs" in data
    assert "health" in data


def test_openapi_schema(client):
    """Verify OpenAPI JSON schema generation and presence of core paths."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert "paths" in schema
    paths = schema["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/races" in paths
    assert "/api/v1/sessions/{session_id}" in paths
    assert "/api/v1/sessions/{session_id}/summary" in paths
    assert "/api/v1/sessions/{session_id}/activity" in paths
    assert "/api/v1/drivers" in paths
    assert "/api/v1/incidents" in paths
    assert "/api/v1/incidents/{incident_id}/telemetry" in paths
    assert "/api/v1/regulations" in paths
    assert "/api/v1/assistant/query" in paths


def test_cors_headers(client):
    """Verify CORS preflight headers on permitted origin."""
    response = client.options(
        "/api/v1/races",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
