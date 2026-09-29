from fastapi.testclient import TestClient

from app.domain.ai import DeterministicFakeAI
from app.main import create_app
from tests.conftest import auth


def test_ramesh_notifications_scope_read_persistence_and_reset(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    db_url = f"sqlite:///{tmp_path / 'notifications.db'}"
    with TestClient(create_app(db_url, ai=DeterministicFakeAI())) as client:
        patient = auth("patient-user-001")
        case = client.post("/api/v1/cases", headers=patient, json={
            "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 30,
            "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z",
            "channel": "manual",
        }).json()
        case_id = case["id"]
        assert client.get("/api/v1/notifications", headers=patient).json() == []
        assert client.post(f"/api/v1/cases/{case_id}/verify", headers=auth("pharmacist-1"),
                           json={"result": "confirmed_stockout", "on_hand": 0}).status_code == 200
        transfer = client.post("/api/v1/transfers/draft", headers=auth("officer-1"),
                               json={"case_id": case_id}).json()
        transfer_id = transfer["id"]
        for action, actor in (("approve", "officer-1"), ("dispatch", "officer-1"),
                              ("receive", "pharmacist-1")):
            assert client.post(f"/api/v1/transfers/{transfer_id}/{action}",
                               headers=auth(actor)).status_code == 200
        assert client.post(f"/api/v1/cases/{case_id}/supply", headers=auth("pharmacist-1"),
                           json={"quantity": 30}).status_code == 200
        assert client.post(f"/api/v1/cases/{case_id}/confirm-received-by-patient",
                           headers=patient).status_code == 200

        notifications = client.get("/api/v1/notifications", headers=patient).json()
        assert [row["kind"] for row in reversed(notifications)] == [
            "on_the_way", "arrived", "given"]
        assert all(set(row) == {"id", "case_id", "kind", "drug_id", "facility_id",
                                "at", "read", "hi", "en"} for row in notifications)
        assert all(row["case_id"] == case_id and row["drug_id"] == "metformin"
                   and row["facility_id"] == "phc-1" and row["read"] is False
                   and row["at"].endswith("Z") for row in notifications)
        assert notifications[1]["hi"] == (
            "आपकी मेटफॉर्मिन सुंदरपुर प्राथमिक स्वास्थ्य केंद्र पहुँच गई है। आज ले लें।")
        assert notifications[1]["en"] == (
            "Your Metformin has reached Sundarpur PHC. Collect it today.")
        events = client.get(f"/api/v1/cases/{case_id}", headers=patient).json()["events"]
        assert {row["id"] for row in notifications} == {
            row["id"] for row in events if row["to_status"] in
            {"dispatched", "received", "supplied"}}
        assert client.get("/api/v1/notifications", headers=auth("asha-1")).json() == notifications
        assert client.get("/api/v1/notifications", headers=auth("asha-2")).json() == []
        assert client.get("/api/v1/notifications", headers=auth("patient-user-002")).json() == []
        assert client.get("/api/v1/notifications", headers=auth("officer-1")).json() == []
        notification_id = notifications[1]["id"]
        path = f"/api/v1/notifications/{notification_id}/read"
        assert client.post(path, headers=auth("patient-user-002")).status_code == 404
        assert client.post(path, headers=auth("officer-1")).status_code == 404
        assert client.post("/api/v1/notifications/unknown/read", headers=patient).status_code == 404
        assert client.post(path, headers=patient).json() == {"id": notification_id, "read": True}
        assert client.get("/api/v1/notifications", headers=patient).json()[1]["read"] is True
        assert client.get("/api/v1/notifications", headers=auth("asha-1")).json()[1]["read"] is False

    with TestClient(create_app(db_url, ai=DeterministicFakeAI())) as client:
        assert client.get("/api/v1/notifications", headers=patient).json()[1]["read"] is True
        assert client.post("/api/v1/demo/reset", headers=auth("officer-1")).status_code == 200
        assert client.get("/api/v1/notifications", headers=patient).json() == []
        assert client.app.state.store.list("notification_read") == []


def test_partial_supply_produces_given_notification():
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        assert client.post("/api/v1/stock", headers=auth("pharmacist-1"), json={
            "drug_id": "metformin", "on_hand": 10,
            "batches": [{"id": "partial-notification-batch", "quantity": 10,
                         "expiry_date": "2027-03-01"}],
        }).status_code == 200
        case = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
            "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 10,
            "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z",
        }).json()
        path = f"/api/v1/cases/{case['id']}"
        assert client.post(f"{path}/verify", headers=auth("pharmacist-1"), json={
            "result": "stock_available", "on_hand": 10}).status_code == 200
        assert client.post(f"{path}/supply", headers=auth("pharmacist-1"), json={
            "quantity": 4}).status_code == 200
        rows = client.get("/api/v1/notifications", headers=auth("patient-user-001")).json()
        assert [row["kind"] for row in rows] == ["given"]
