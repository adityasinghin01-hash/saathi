from tests.conftest import auth

BODY = {"patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 30,
        "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual"}


def test_post_idempotency_key_replays_response(client):
    headers = {**auth("patient-user-001"), "Idempotency-Key": "test-post-1"}
    first = client.post("/api/v1/cases", headers=headers, json=BODY)
    again = client.post("/api/v1/cases", headers=headers, json=BODY)
    assert first.status_code == 200
    assert again.json()["id"] == first.json()["id"]
    changed = client.post("/api/v1/cases", headers=headers, json={**BODY, "requested_qty": 31})
    assert changed.status_code == 409


def test_batch_ignores_duplicate_op_ids(client):
    op = {"op_id": "offline-1", "method": "POST", "path": "/api/v1/cases", "body": BODY}
    first = client.post("/api/v1/sync/batch", headers=auth("patient-user-001"), json={"ops": [op]})
    again = client.post("/api/v1/sync/batch", headers=auth("patient-user-001"), json={"ops": [op]})
    assert first.status_code == 200
    assert first.json()["results"][0]["status"] == "applied"
    assert again.json()["results"][0]["status"] == "duplicate"
    assert again.json()["results"][0]["result"]["id"] == first.json()["results"][0]["result"]["id"]


def test_batch_accepts_contract_relative_path(client):
    op = {"op_id": "relative-1", "method": "POST", "path": "/cases", "body": BODY}
    response = client.post("/api/v1/sync/batch", headers=auth("patient-user-001"), json={"ops": [op]})
    assert response.status_code == 200
    assert response.json()["results"][0]["status"] == "applied"
    assert response.json()["results"][0]["result"]["patient_id"] == "patient-001"
