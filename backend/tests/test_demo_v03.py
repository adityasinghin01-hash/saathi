from datetime import date

from fastapi.testclient import TestClient

from app.domain.ai import DeterministicFakeAI
from app.domain.transfers import select_donor
from app.main import create_app
from tests.conftest import auth


def test_demo_reset_and_scenario(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        scenario = client.get("/api/v1/demo/scenario/ramesh", headers=auth("officer-1"))
        assert scenario.status_code == 200
        ids = scenario.json()
        assert ids == {"patient_id": "patient-001", "asha_id": "asha-1",
                       "pharmacist_id": "pharmacist-1", "district_officer_id": "officer-1",
                       "facility_id": "phc-1", "donor_facility_id": "phc-2",
                       "drug_id": "metformin"}
        case = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
            "patient_id": ids["patient_id"], "drug_id": ids["drug_id"],
            "requested_qty": 30, "household_supply_days": 0,
            "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual"})
        assert case.status_code == 200
        reset = client.post("/api/v1/demo/reset", headers=auth("pharmacist-1"))
        assert reset.status_code == 200
        assert reset.json()["ok"] is True
        assert reset.json()["seeded_at"].endswith("Z")
        assert client.get("/api/v1/cases", headers=auth("patient-user-001")).json() == []
        assert client.get("/api/v1/demo/scenario/ramesh", headers=auth("officer-1")).json() == ids


def test_demo_reset_disabled_and_auth_required(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        assert client.post("/api/v1/demo/reset", headers=auth("officer-1")).status_code == 403
        assert client.get("/api/v1/demo/scenario/ramesh").status_code == 401


def test_ramesh_has_only_one_feasible_phc_donor():
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        store = client.app.state.store
        case = {"facility_id": "phc-1", "drug_id": "metformin", "requested_qty": 30}
        donor = select_donor(store, case, date(2026, 9, 28))
        assert donor["donor"]["id"] == "phc-2"
        snapshot = store.get("stock_snapshot", "stock-phc-2-metformin")
        snapshot["on_hand"] = 0
        snapshot["batches"] = []
        store.put("stock_snapshot", snapshot)
        assert select_donor(store, case, date(2026, 9, 28)) is None
