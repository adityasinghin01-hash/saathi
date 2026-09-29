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


def test_frontend_queued_case_replay_creates_one_case(client):
    op = {"op_id": "frontend-case-replay", "method": "POST", "path": "/cases",
          "body": {"patient_id": "patient-001", "drug_id": "metformin",
                   "requested_qty": 30, "household_supply_days": 0,
                   "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual",
                   "transcript": None}}
    before = {row["id"] for row in client.get(
        "/api/v1/cases", headers=auth("patient-user-001")).json()}
    first = client.post("/api/v1/sync/batch", headers=auth("patient-user-001"),
                        json={"ops": [op]})
    second = client.post("/api/v1/sync/batch", headers=auth("patient-user-001"),
                         json={"ops": [op]})
    assert first.status_code == second.status_code == 200
    first_result = first.json()["results"][0]
    second_result = second.json()["results"][0]
    assert first_result["status"] == "applied"
    assert second_result == {"op_id": op["op_id"], "status": "duplicate",
                             "result": first_result["result"]}
    after = {row["id"] for row in client.get(
        "/api/v1/cases", headers=auth("patient-user-001")).json()}
    assert after - before == {first_result["result"]["id"]}


def test_frontend_batch_missing_required_field_is_per_op_error(client):
    good_body = {"patient_id": "patient-001", "drug_id": "metformin",
                 "requested_qty": 30, "household_supply_days": 0,
                 "attempted_at": "2026-09-28T09:00:00Z", "channel": "voice",
                 "transcript": "कल मेटफॉर्मिन नहीं मिली।"}
    ops = [
        {"op_id": "frontend-missing-field", "method": "POST", "path": "/cases",
         "body": {key: value for key, value in good_body.items() if key != "drug_id"}},
        {"op_id": "frontend-valid-after-error", "method": "POST", "path": "/cases",
         "body": good_body},
    ]
    before = {row["id"] for row in client.get(
        "/api/v1/cases", headers=auth("patient-user-001")).json()}
    response = client.post("/api/v1/sync/batch", headers=auth("patient-user-001"),
                           json={"ops": ops})
    assert response.status_code == 200
    failed, applied = response.json()["results"]
    assert failed["op_id"] == "frontend-missing-field"
    assert failed["status"] == "error"
    assert failed["error"]["code"] == "validation_error"
    assert applied["op_id"] == "frontend-valid-after-error"
    assert applied["status"] == "applied"
    after = {row["id"] for row in client.get(
        "/api/v1/cases", headers=auth("patient-user-001")).json()}
    assert after - before == {applied["result"]["id"]}
