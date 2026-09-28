from tests.conftest import auth


def test_transfer_provider_failure_uses_marked_fallback(client):
    from app.domain.ai import AIUnavailable

    class Unavailable:
        def transfer_rationale(self, *args):
            raise AIUnavailable("failed")

    case_id = new_verified_case(client)
    previous = client.app.state.ai
    client.app.state.ai = Unavailable()
    try:
        response = client.post("/api/v1/transfers/draft", headers=auth("officer-1"),
                               json={"case_id": case_id})
    finally:
        client.app.state.ai = previous
    assert response.status_code == 200
    assert response.json()["ai_source"] == "fallback"


def new_verified_case(client, requested_qty=30):
    case = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
        "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": requested_qty,
        "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual",
    }).json()
    client.post(f"/api/v1/cases/{case['id']}/verify", headers=auth("pharmacist-1"),
                json={"result": "confirmed_stockout", "on_hand": 0})
    return case["id"]


def test_transfer_needs_human_approval_and_receiving_facility(client):
    case_id = new_verified_case(client)
    response = client.post("/api/v1/transfers/draft", headers=auth("officer-1"),
                           json={"case_id": case_id})
    assert response.status_code == 200
    transfer = response.json()
    assert transfer["status"] == "draft"
    assert transfer["constraints_checked"] == {"donor_safety_stock_ok": True,
                                                "expiry_ok": True, "units_ok": True}
    assert transfer["to_facility_id"] == "phc-1"
    assert client.post(f"/api/v1/transfers/{transfer['id']}/dispatch",
                       headers=auth("officer-1")).status_code == 409
    assert client.post(f"/api/v1/transfers/{transfer['id']}/approve",
                       headers=auth("patient-user-001")).status_code == 403
    assert client.post(f"/api/v1/transfers/{transfer['id']}/approve",
                       headers=auth("officer-1")).json()["status"] == "approved"
    assert client.post(f"/api/v1/transfers/{transfer['id']}/dispatch",
                       headers=auth("officer-1")).json()["status"] == "dispatched"
    assert client.post(f"/api/v1/transfers/{transfer['id']}/receive",
                       headers=auth("pharmacist-2")).status_code == 403
    assert client.post(f"/api/v1/transfers/{transfer['id']}/receive",
                       headers=auth("pharmacist-1")).json()["status"] == "received"
    assert client.get(f"/api/v1/cases/{case_id}", headers=auth("patient-user-001")).json()["status"] == "received"


def test_no_feasible_transfer_keeps_case_verified(client):
    case_id = new_verified_case(client, requested_qty=100000)
    response = client.post("/api/v1/transfers/draft", headers=auth("officer-1"),
                           json={"case_id": case_id})
    assert response.status_code == 200
    assert response.json()["status"] == "no_feasible_transfer"
    assert response.json()["ai_source"] == "fallback"
    case = client.get(f"/api/v1/cases/{case_id}", headers=auth("officer-1")).json()
    assert case["status"] == "verified"
    assert case["escalated"] is True
