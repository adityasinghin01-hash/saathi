from fastapi.testclient import TestClient

from app.main import create_app


def test_health():
    with TestClient(create_app("sqlite:///:memory:")) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "label": "Synthetic demo data"}
