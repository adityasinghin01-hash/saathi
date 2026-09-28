from tests.conftest import auth


def test_case_creation_rejects_medical_advice_transcript(client):
    response = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
        "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 30,
        "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z",
        "channel": "voice", "transcript": "Take two tablets daily.",
    })
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "medical_advice"


def test_reference_and_patient_access(client):
    assert client.get("/api/v1/demo/users").status_code == 200
    assert len(client.get("/api/v1/facilities", headers=auth("officer-1")).json()) == 7
    assert len(client.get("/api/v1/drugs", headers=auth("officer-1")).json()) == 4
    assert client.get("/api/v1/me", headers=auth("asha-1")).json()["role"] == "asha"
    assert client.get("/api/v1/patients/patient-001", headers=auth("patient-user-001")).status_code == 200
    assert client.get("/api/v1/patients/patient-002", headers=auth("patient-user-001")).status_code == 403
    assert client.get("/api/v1/patients/patient-001", headers=auth("officer-1")).status_code == 403


def test_report_verify_and_illegal_transition(client):
    response = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
        "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 30,
        "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual",
    })
    assert response.status_code == 200
    case = response.json()
    assert case["status"] == "reported"
    case_id = case["id"]
    assert client.post(f"/api/v1/cases/{case_id}/verify", headers=auth("patient-user-001"),
                       json={"result": "confirmed_stockout", "on_hand": 0}).status_code == 403
    assert client.get(f"/api/v1/cases/{case_id}", headers=auth("patient-user-002")).status_code == 403
    assert client.post(f"/api/v1/cases/{case_id}/supply", headers=auth("pharmacist-1"),
                       json={"quantity": 30}).status_code == 409
    verified = client.post(f"/api/v1/cases/{case_id}/verify", headers=auth("pharmacist-1"),
                           json={"result": "confirmed_stockout", "on_hand": 0})
    assert verified.status_code == 200
    detail = client.get(f"/api/v1/cases/{case_id}", headers=auth("patient-user-001")).json()
    assert [e["to_status"] for e in detail["events"]] == ["reported", "verified"]
    assert client.get("/api/v1/cases", headers=auth("pharmacist-2")).json() == []
    assert len(client.get("/api/v1/cases?status=verified", headers=auth("officer-1")).json()) >= 1


def test_household_only_closes_without_transfer(client):
    case = client.post("/api/v1/cases", headers=auth("asha-1"), json={
        "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 15,
        "household_supply_days": 5, "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual",
    }).json()
    response = client.post(f"/api/v1/cases/{case['id']}/verify", headers=auth("pharmacist-1"),
                           json={"result": "household_only", "on_hand": 20})
    assert response.json()["status"] == "closed"
    assert len(client.get(f"/api/v1/cases/{case['id']}", headers=auth("asha-1")).json()["events"]) == 3


def test_stock_available_supply_deducts_stock(client):
    client.post("/api/v1/stock", headers=auth("pharmacist-1"), json={
        "drug_id": "metformin", "on_hand": 20,
        "batches": [{"id": "supply-batch", "quantity": 20, "expiry_date": "2027-03-01"}],
    })
    case = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
        "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 10,
        "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual",
    }).json()
    client.post(f"/api/v1/cases/{case['id']}/verify", headers=auth("pharmacist-1"),
                json={"result": "stock_available", "on_hand": 20})
    partial = client.post(f"/api/v1/cases/{case['id']}/supply", headers=auth("pharmacist-1"),
                          json={"quantity": 1})
    assert partial.status_code == 200
    assert partial.json()["status"] == "partially_supplied"
    assert partial.json()["received_qty"] == 1
    supplied = client.post(f"/api/v1/cases/{case['id']}/supply", headers=auth("pharmacist-1"),
                           json={"quantity": 9})
    assert supplied.status_code == 200
    assert supplied.json()["status"] == "supplied"
    assert supplied.json()["received_qty"] == 10
    from app.domain.forecast import latest_snapshot
    snapshot = latest_snapshot(client.app.state.store, "phc-1", "metformin")
    assert snapshot["on_hand"] == 10
    assert any(row["patient_id"] == "patient-001" and row["quantity"] == 1
               for row in client.app.state.store.list("dispensing"))
    assert any(row["patient_id"] == "patient-001" and row["quantity"] == 9
               for row in client.app.state.store.list("dispensing"))
