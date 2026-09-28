from tests.conftest import auth


def test_ramesh_report_to_close(client):
    reported = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
        "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 30,
        "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual",
    }).json()
    case_id = reported["id"]
    assert reported["status"] == "reported"

    verified = client.post(f"/api/v1/cases/{case_id}/verify", headers=auth("pharmacist-1"),
                           json={"result": "confirmed_stockout", "on_hand": 0}).json()
    assert verified["status"] == "verified"
    transfer = client.post("/api/v1/transfers/draft", headers=auth("officer-1"),
                           json={"case_id": case_id}).json()
    assert transfer["status"] == "draft"
    transfer_id = transfer["id"]
    assert client.post(f"/api/v1/transfers/{transfer_id}/approve",
                       headers=auth("officer-1")).json()["status"] == "approved"
    assert client.post(f"/api/v1/transfers/{transfer_id}/dispatch",
                       headers=auth("officer-1")).json()["status"] == "dispatched"
    assert client.post(f"/api/v1/transfers/{transfer_id}/receive",
                       headers=auth("pharmacist-1")).json()["status"] == "received"
    supplied = client.post(f"/api/v1/cases/{case_id}/supply", headers=auth("pharmacist-1"),
                           json={"quantity": 30}).json()
    assert supplied["status"] == "supplied"
    closed = client.post(f"/api/v1/cases/{case_id}/confirm-received-by-patient",
                         headers=auth("patient-user-001")).json()
    assert closed["status"] == "closed"
    detail = client.get(f"/api/v1/cases/{case_id}", headers=auth("officer-1")).json()
    assert [event["to_status"] for event in detail["events"]] == [
        "reported", "verified", "transfer_drafted", "transfer_approved",
        "dispatched", "received", "supplied", "closed",
    ]
    assert detail["transfer"]["status"] == "received"


def test_rejected_transfer_cannot_dispatch(client):
    case = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
        "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 20,
        "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual",
    }).json()
    client.post(f"/api/v1/cases/{case['id']}/verify", headers=auth("pharmacist-1"),
                json={"result": "confirmed_stockout", "on_hand": 0})
    transfer = client.post("/api/v1/transfers/draft", headers=auth("officer-1"),
                           json={"case_id": case["id"]}).json()
    rejected = client.post(f"/api/v1/transfers/{transfer['id']}/reject",
                           headers=auth("officer-1"))
    assert rejected.json()["status"] == "rejected"
    assert client.post(f"/api/v1/transfers/{transfer['id']}/dispatch",
                       headers=auth("officer-1")).status_code == 409
    replacement = client.post("/api/v1/transfers/draft", headers=auth("officer-1"),
                              json={"case_id": case["id"]})
    assert replacement.status_code == 200
    assert replacement.json()["status"] == "draft"
    assert replacement.json()["id"] != transfer["id"]


def test_cancel_requires_note_and_writes_event(client):
    case = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
        "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 10,
        "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual",
    }).json()
    path = f"/api/v1/cases/{case['id']}/cancel"
    assert client.post(path, headers=auth("patient-user-002"), json={"note": "duplicate"}).status_code == 403
    assert client.post(path, headers=auth("patient-user-001"), json={"note": ""}).status_code == 422
    assert client.post(path, headers=auth("patient-user-001"),
                       json={"note": "Synthetic duplicate report"}).json()["status"] == "cancelled"
    detail = client.get(f"/api/v1/cases/{case['id']}", headers=auth("patient-user-001")).json()
    assert detail["events"][-1]["note"] == "Synthetic duplicate report"
