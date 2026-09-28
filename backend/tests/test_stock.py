from tests.conftest import auth


def test_stock_scope_and_overview(client):
    payload = {"drug_id": "metformin", "on_hand": 10, "batches": [
        {"id": "new-batch-1", "quantity": 10, "expiry_date": "2027-03-01"}], "source": "manual"}
    assert client.post("/api/v1/stock", headers=auth("patient-user-001"), json=payload).status_code == 403
    response = client.post("/api/v1/stock", headers=auth("pharmacist-1"), json=payload)
    assert response.status_code == 200
    assert response.json()["on_hand"] == 10
    assert response.json()["recorded_at"].endswith("Z")
    assert client.get("/api/v1/district/overview", headers=auth("pharmacist-1")).status_code == 403
    overview = client.get("/api/v1/district/overview?district=Suryanagar",
                          headers=auth("officer-1"))
    assert overview.status_code == 200
    rows = overview.json()
    assert len(rows) == 28
    row = next(r for r in rows if r["facility_id"] == "phc-1" and r["drug_id"] == "metformin")
    assert row["on_hand"] == 10
    assert row["recorded_at"] == response.json()["recorded_at"]
    assert row["combined"] == max(row["cohort_need"], row["dispensing_forecast"])


def test_stock_rejects_mismatched_batch_sum(client):
    response = client.post("/api/v1/stock", headers=auth("pharmacist-1"), json={
        "drug_id": "metformin", "on_hand": 10,
        "batches": [{"id": "bad", "quantity": 9, "expiry_date": "2027-03-01"}],
    })
    assert response.status_code == 422


def test_stock_rejects_invalid_expiry(client):
    response = client.post("/api/v1/stock", headers=auth("pharmacist-1"), json={
        "drug_id": "metformin", "on_hand": 10,
        "batches": [{"id": "bad-date", "quantity": 10, "expiry_date": "not-a-date"}],
    })
    assert response.status_code == 422


def test_overview_calibrated_setting_uses_additive_components(client, monkeypatch):
    monkeypatch.setenv("DEMAND_RULE", "calibrated")
    response = client.get("/api/v1/district/overview", headers=auth("officer-1"))
    assert response.status_code == 200
    row = next(row for row in response.json()
               if row["facility_id"] == "phc-1" and row["drug_id"] == "metformin")
    assert row["demand_rule"] == "calibrated"
    assert row["combined"] == (row["calibrated_cohort_need"]
                               + row["unenrolled_dispensing_forecast"])
