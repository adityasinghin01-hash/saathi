import json

from fastapi.testclient import TestClient

from app.domain.ai import DeterministicFakeAI
from app.main import create_app
from tests.conftest import auth


def test_evaluation_summary_scoped_and_reads_results(monkeypatch, tmp_path):
    (tmp_path / "forecast.json").write_text(json.dumps({"repetitions": 12}))
    (tmp_path / "extraction.json").write_text(json.dumps({"samples": 30}))
    monkeypatch.setenv("EVALUATION_RESULTS_DIR", str(tmp_path))
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        response = client.get("/api/v1/evaluation/summary", headers=auth("officer-1"))
        assert response.status_code == 200
        assert response.json()["forecast"]["repetitions"] == 12
        assert response.json()["extraction"]["samples"] == 30
        assert client.get("/api/v1/evaluation/summary",
                          headers=auth("pharmacist-1")).status_code == 403
        assert client.get("/api/v1/evaluation/summary").status_code == 401


def test_cors_uses_configured_origins(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://demo.example, https://other.example")
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        allowed = client.options("/api/v1/cases", headers={
            "Origin": "https://demo.example", "Access-Control-Request-Method": "POST"})
        assert allowed.headers["access-control-allow-origin"] == "https://demo.example"
        denied = client.options("/api/v1/cases", headers={
            "Origin": "https://wrong.example", "Access-Control-Request-Method": "POST"})
        assert "access-control-allow-origin" not in denied.headers


def test_cors_defaults_to_localhost_3000(monkeypatch):
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        response = client.options("/api/v1/cases", headers={
            "Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
