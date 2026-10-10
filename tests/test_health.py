"""Test health check endpoint."""
from fastapi.testclient import TestClient


def test_health_check_returns_healthy(client: TestClient):
    """Verify GET /health returns status 200 with service metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "CloudCart" in data["service"]
    assert "timestamp" in data
