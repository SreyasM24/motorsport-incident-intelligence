"""Integration tests for API v1 route handlers and error conditions."""

def test_get_races_empty(client):
    """Verify races endpoint returns empty list when no races exist."""
    response = client.get("/api/v1/races")
    assert response.status_code == 200
    assert response.json() == []


def test_get_race_not_found(client):
    """Verify nonexistent race returns structured 404 error."""
    response = client.get("/api/v1/races/non-existent-race")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "non-existent-race" in data["error"]["message"]


def test_get_session_not_found(client):
    """Verify nonexistent session returns structured 404 error."""
    response = client.get("/api/v1/sessions/non-existent-session")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_get_drivers_empty(client):
    """Verify drivers endpoint returns empty list when no drivers ingested."""
    response = client.get("/api/v1/drivers")
    assert response.status_code == 200
    assert response.json() == []


def test_get_driver_not_found(client):
    """Verify nonexistent driver returns 404."""
    response = client.get("/api/v1/drivers/XYZ")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_get_incidents_empty(client):
    """Verify incidents endpoint returns empty list when no incidents recorded."""
    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    assert response.json() == []


def test_get_incident_not_found(client):
    """Verify nonexistent incident returns 404."""
    response = client.get("/api/v1/incidents/INC-999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_get_incident_telemetry_not_found(client):
    """Verify nonexistent incident telemetry returns 404."""
    response = client.get("/api/v1/incidents/INC-999/telemetry")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_get_regulations_empty(client):
    """Verify regulations endpoint returns empty list when database empty."""
    response = client.get("/api/v1/regulations")
    assert response.status_code == 200
    assert response.json() == []


def test_assistant_query(client):
    """Verify AI Steward Assistant endpoint returns factual decision-support response."""
    response = client.post(
        "/api/v1/assistant/query",
        json={"query": "Why was this incident flagged?", "incident_id": "INC-024"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sender"] == "assistant"
    assert "PROXIMITY" in data["text"]
    assert len(data["evidenceChips"]) > 0
    assert len(data["suggestedFollowUps"]) > 0


def test_update_incident_status_invalid(client):
    """Verify invalid status string returns 422 validation error."""
    response = client.patch(
        "/api/v1/incidents/INC-024/status",
        json={"status": "INVALID_STATUS"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] in ("VALIDATION_ERROR", "REQUEST_VALIDATION_ERROR")
