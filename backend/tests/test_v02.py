from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import auth

REPORT = {"patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 12,
          "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual"}


def report_verified(client):
    case = client.post("/api/v1/cases", headers=auth("patient-user-001"), json=REPORT).json()
    response = client.post(f"/api/v1/cases/{case['id']}/verify", headers=auth("pharmacist-1"),
                           json={"result": "confirmed_stockout", "on_hand": 0})
    assert response.status_code == 200
    return case["id"]


def draft(client, case_id):
    response = client.post("/api/v1/transfers/draft", headers=auth("officer-1"),
                           json={"case_id": case_id})
    assert response.status_code == 200
    return response.json()["id"]


def test_rejection_returns_case_to_verified_with_audit_event(client):
    case_id = report_verified(client)
    transfer_id = draft(client, case_id)
    response = client.post(f"/api/v1/transfers/{transfer_id}/reject", headers=auth("officer-1"))
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    detail = client.get(f"/api/v1/cases/{case_id}", headers=auth("officer-1")).json()
    assert detail["status"] == "verified"
    assert detail["events"][-1]["from_status"] == "transfer_drafted"
    assert detail["events"][-1]["to_status"] == "verified"
    assert draft(client, case_id) != transfer_id


def test_cancellation_before_dispatch_cancels_transfer_and_blocks_actions(client):
    case_id = report_verified(client)
    transfer_id = draft(client, case_id)
    client.post(f"/api/v1/transfers/{transfer_id}/approve", headers=auth("officer-1"))
    response = client.post(f"/api/v1/cases/{case_id}/cancel", headers=auth("asha-1"),
                           json={"note": "Patient moved"})
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    detail = client.get(f"/api/v1/cases/{case_id}", headers=auth("officer-1")).json()
    assert detail["transfer"]["status"] == "cancelled"
    assert detail["events"][-1]["note"] == "Patient moved"
    assert client.post(f"/api/v1/transfers/{transfer_id}/dispatch",
                       headers=auth("officer-1")).status_code == 409
    assert client.post(f"/api/v1/cases/{case_id}/cancel", headers=auth("officer-1"),
                       json={"note": "Again"}).status_code == 409


def test_dispatched_transfer_is_received_after_case_cancellation(client):
    case_id = report_verified(client)
    transfer_id = draft(client, case_id)
    client.post(f"/api/v1/transfers/{transfer_id}/approve", headers=auth("officer-1"))
    client.post(f"/api/v1/transfers/{transfer_id}/dispatch", headers=auth("officer-1"))
    cancelled = client.post(f"/api/v1/cases/{case_id}/cancel", headers=auth("pharmacist-1"),
                            json={"note": "Patient moved after dispatch"})
    assert cancelled.status_code == 200
    received = client.post(f"/api/v1/transfers/{transfer_id}/receive",
                           headers=auth("pharmacist-1"))
    assert received.status_code == 200
    assert received.json()["status"] == "received"
    detail = client.get(f"/api/v1/cases/{case_id}", headers=auth("officer-1")).json()
    assert detail["status"] == "cancelled"
    assert detail["received_qty"] == 0
    assert client.post(f"/api/v1/cases/{case_id}/supply", headers=auth("pharmacist-1"),
                       json={"quantity": 1}).status_code == 409


def test_district_horizon_and_drug_rule(client):
    headers = auth("officer-1")
    default = client.get("/api/v1/district/overview", headers=headers)
    week = client.get("/api/v1/district/overview?horizon_days=7", headers=headers)
    assert default.status_code == week.status_code == 200
    default_row = next(row for row in default.json() if row["facility_id"] == "phc-1"
                       and row["drug_id"] == "metformin")
    week_row = next(row for row in week.json() if row["facility_id"] == "phc-1"
                    and row["drug_id"] == "metformin")
    assert default_row["horizon_days"] == 30
    assert week_row["horizon_days"] == 7
    assert week_row["cohort_need"] * 30 == default_row["cohort_need"] * 7
    assert client.get("/api/v1/district/overview?horizon_days=90",
                      headers=headers).status_code == 200
    for invalid in (6, 91, "abc"):
        assert client.get(f"/api/v1/district/overview?horizon_days={invalid}",
                          headers=headers).status_code == 422
    store = client.app.state.store
    drug = store.get("drug", "metformin")
    assert drug["demand_rule"] == "max"
    store.put("drug", {**drug, "demand_rule": "dispensing_only"})
    changed = client.get("/api/v1/district/overview?horizon_days=7", headers=headers)
    row = next(row for row in changed.json() if row["facility_id"] == "phc-1"
               and row["drug_id"] == "metformin")
    assert row["combined"] == row["dispensing_forecast"]
    store.put("drug", drug)


def test_no_feasible_transfer_has_v02_reason(client):
    case = client.post("/api/v1/cases", headers=auth("patient-user-001"),
                       json={**REPORT, "requested_qty": 100000}).json()
    client.post(f"/api/v1/cases/{case['id']}/verify", headers=auth("pharmacist-1"),
                json={"result": "confirmed_stockout", "on_hand": 0})
    result = client.post("/api/v1/transfers/draft", headers=auth("officer-1"),
                         json={"case_id": case["id"]}).json()
    assert result["status"] == "no_feasible_transfer"
    assert result["reason"] == "needs_split_or_supply"


def test_sync_independent_ops_and_method_validation(client):
    ops = [
        {"op_id": "bad-method-v02", "method": "GET", "path": "/api/v1/cases", "body": REPORT},
        {"op_id": "bad-body-v02", "method": "POST", "path": "/api/v1/cases",
         "body": {**REPORT, "requested_qty": 0}},
        {"op_id": "good-v02", "method": "POST", "path": "/api/v1/cases", "body": REPORT},
    ]
    response = client.post("/api/v1/sync/batch", headers=auth("patient-user-001"),
                           json={"ops": ops})
    assert response.status_code == 200
    results = response.json()["results"]
    assert [row["status"] for row in results] == ["error", "error", "applied"]
    assert all(row["op_id"] for row in results)
    assert all("error" in row for row in results[:2])
    assert results[2]["result"]["status"] == "reported"
    repeated = client.post("/api/v1/sync/batch", headers=auth("patient-user-001"),
                           json={"ops": [ops[2]]}).json()["results"][0]
    assert repeated["status"] == "duplicate"
    assert repeated["result"]["id"] == results[2]["result"]["id"]


def test_partial_supply_rejects_overfill_and_keeps_stock_consistent():
    with TestClient(create_app("sqlite:///:memory:")) as client:
        stock = {"drug_id": "metformin", "on_hand": 20,
                 "batches": [{"id": "partial-batch", "quantity": 20,
                              "expiry_date": "2027-03-01"}]}
        assert client.post("/api/v1/stock", headers=auth("pharmacist-1"),
                           json=stock).status_code == 200
        case = client.post("/api/v1/cases", headers=auth("patient-user-001"), json=REPORT).json()
        path = f"/api/v1/cases/{case['id']}"
        client.post(f"{path}/verify", headers=auth("pharmacist-1"),
                    json={"result": "stock_available", "on_hand": 20})
        first = client.post(f"{path}/supply", headers=auth("pharmacist-1"),
                            json={"quantity": 4}).json()
        second = client.post(f"{path}/supply", headers=auth("pharmacist-1"),
                             json={"quantity": 3}).json()
        assert (first["status"], first["received_qty"]) == ("partially_supplied", 4)
        assert (second["status"], second["received_qty"]) == ("partially_supplied", 7)
        assert client.post(f"{path}/supply", headers=auth("pharmacist-1"),
                           json={"quantity": 6}).status_code == 422
        done = client.post(f"{path}/supply", headers=auth("pharmacist-1"),
                           json={"quantity": 5}).json()
        assert (done["status"], done["received_qty"]) == ("supplied", 12)
        detail = client.get(path, headers=auth("patient-user-001")).json()
        assert [event["to_status"] for event in detail["events"]] == [
            "reported", "verified", "partially_supplied", "partially_supplied", "supplied"]
        from app.domain.forecast import latest_snapshot
        assert latest_snapshot(client.app.state.store, "phc-1", "metformin")["on_hand"] == 8
