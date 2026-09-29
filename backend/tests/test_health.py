import time

from fastapi.testclient import TestClient

from app.main import create_app


def test_health():
    with TestClient(create_app("sqlite:///:memory:")) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "label": "Synthetic demo data"}


def test_health_answers_under_50_ms_without_storage_or_ai(monkeypatch):
    with TestClient(create_app("sqlite:///:memory:")) as client:
        def unexpected_call(*args, **kwargs):
            raise AssertionError("health must not access storage or AI")

        monkeypatch.setattr(client.app.state.store, "get", unexpected_call)
        monkeypatch.setattr(client.app.state.store, "list", unexpected_call)
        monkeypatch.setattr(client.app.state.ai, "extract_voice", unexpected_call)
        client.get("/api/v1/health")  # Warm the TestClient transport.
        started = time.perf_counter()
        response = client.get("/api/v1/health")
        elapsed = time.perf_counter() - started
    assert response.status_code == 200
    assert elapsed < 0.050, f"health took {elapsed * 1000:.1f} ms"
