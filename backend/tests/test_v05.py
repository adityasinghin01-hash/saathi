from fastapi.testclient import TestClient

from app.domain.ai import DeterministicFakeAI
from app.domain.forecast import dispensing_series
from app.main import create_app
from tests.conftest import auth


def fresh_client():
    return TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI()))


def report_and_draft(client):
    case = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
        "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 30,
        "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z",
        "channel": "manual",
    }).json()
    assert client.post(f"/api/v1/cases/{case['id']}/verify", headers=auth("pharmacist-1"),
                       json={"result": "confirmed_stockout", "on_hand": 0}).status_code == 200
    transfer = client.post("/api/v1/transfers/draft", headers=auth("officer-1"),
                           json={"case_id": case["id"]}).json()
    return case, transfer


def test_patients_list_is_scoped_and_includes_prescriptions_and_open_case():
    with fresh_client() as client:
        case, _ = report_and_draft(client)
        patient = client.get("/api/v1/patients", headers=auth("patient-user-001"))
        assert patient.status_code == 200
        assert [row["id"] for row in patient.json()] == ["patient-001"]
        assert patient.json()[0]["name"] == "Ramesh"
        assert patient.json()[0]["name_hi"] == "रमेश"
        assert patient.json()[0]["age"] == 54
        assert patient.json()[0]["open_case"]["id"] == case["id"]
        assert patient.json()[0]["prescriptions"][0]["drug_id"] == "metformin"
        asha = client.get("/api/v1/patients", headers=auth("asha-1")).json()
        assert asha and all(row["asha_id"] == "asha-1" for row in asha)
        pharmacist = client.get("/api/v1/patients", headers=auth("pharmacist-1")).json()
        assert pharmacist and all(row["facility_id"] == "phc-1" for row in pharmacist)
        officer = client.get("/api/v1/patients", headers=auth("officer-1")).json()
        assert len(officer) == 60
        assert client.get("/api/v1/patients", headers=auth("unknown")).status_code == 401
        client.app.state.store.put("user", {"id": "visitor", "role": "visitor",
                                            "facility_id": "phc-1"})
        assert client.get("/api/v1/patients", headers=auth("visitor")).status_code == 403


def test_transfers_list_filters_scope_and_detail_rejects_wrong_role():
    with fresh_client() as client:
        case, transfer = report_and_draft(client)
        path = "/api/v1/transfers"
        officer = client.get(path, headers=auth("officer-1"))
        assert officer.status_code == 200
        assert officer.json()[0]["case_id"] == case["id"]
        assert officer.json()[0]["batch_allocations"][0]["expiry_date"]
        assert officer.json()[0]["ai_source"] == "fake"
        assert client.get(path + "?status=approved", headers=auth("officer-1")).json() == []
        assert [row["id"] for row in client.get(
            path + "?facility_id=phc-2", headers=auth("pharmacist-2")).json()] == [transfer["id"]]
        assert client.get(path, headers=auth("pharmacist-3")).json() == []
        assert client.get(path + "?facility_id=phc-1",
                          headers=auth("pharmacist-2")).status_code == 403
        assert client.get(path, headers=auth("patient-user-001")).status_code == 403
        detail = client.get(f"{path}/{transfer['id']}", headers=auth("pharmacist-1"))
        assert detail.status_code == 200
        assert detail.json()["id"] == transfer["id"]
        assert client.get(f"{path}/{transfer['id']}", headers=auth("pharmacist-3")).status_code == 403
        assert client.get(f"{path}/{transfer['id']}", headers=auth("asha-1")).status_code == 403


def test_district_scope_excludes_other_district_records():
    with fresh_client() as client:
        _, transfer = report_and_draft(client)
        store = client.app.state.store
        store.put("facility", {"id": "remote-phc", "name": "Remote PHC",
                               "district": "Elsewhere"})
        store.put("patient", {"id": "remote-patient", "facility_id": "remote-phc",
                              "asha_id": "asha-remote", "name": "Remote"})
        store.put("stock_snapshot", {"id": "remote-stock", "facility_id": "remote-phc",
                                     "drug_id": "metformin", "recorded_at": "2026-09-28T08:00:00Z",
                                     "on_hand": 8, "batches": [], "recorded_by": "remote",
                                     "source": "manual"})
        store.put("transfer", {**transfer, "id": "remote-transfer",
                               "to_facility_id": "remote-phc"})
        assert all(row["id"] != "remote-patient" for row in client.get(
            "/api/v1/patients", headers=auth("officer-1")).json())
        assert client.get("/api/v1/stock?facility_id=remote-phc",
                          headers=auth("officer-1")).status_code == 403
        assert client.get("/api/v1/district/series?facility_id=remote-phc&drug_id=metformin",
                          headers=auth("officer-1")).status_code == 403
        assert all(row["id"] != "remote-transfer" for row in client.get(
            "/api/v1/transfers", headers=auth("officer-1")).json())
        assert client.get("/api/v1/transfers/remote-transfer",
                          headers=auth("officer-1")).status_code == 403


def test_series_uses_seeded_stock_and_dispensing_history_with_forecast_values():
    with fresh_client() as client:
        url = "/api/v1/district/series?facility_id=phc-1&drug_id=metformin"
        response = client.get(url, headers=auth("officer-1"))
        assert response.status_code == 200
        body = response.json()
        assert body["facility_id"] == "phc-1" and body["drug_id"] == "metformin"
        assert len(body["days"]) == 60
        assert body["days"][-1]["date"] == "2026-09-28"
        assert body["days"][-1]["on_hand"] == 0
        assert all(day["stockout"] == (day["on_hand"] == 0) for day in body["days"])
        assert all(day["dispensed"] == 0 for day in body["days"] if day["stockout"])
        assert len(client.get(url + "&days=7", headers=auth("officer-1")).json()["days"]) == 7
        assert client.get(url + "&days=0", headers=auth("officer-1")).status_code == 422
        overview = client.get("/api/v1/district/overview", headers=auth("officer-1")).json()
        row = next(row for row in overview if row["facility_id"] == "phc-1"
                   and row["drug_id"] == "metformin")
        assert body["horizon_days"] == row["horizon_days"] == 30
        assert body["cohort_need_daily"] == row["cohort_need"] / 30
        assert body["dispensing_forecast_daily"] == row["dispensing_forecast"] / 30
        assert body["combined_daily"] == row["combined"] / 30
        assert body["days_left"] == row["days_left"]
        assert client.get(url, headers=auth("pharmacist-1")).status_code == 403
        assert client.get(url.replace("phc-1", "missing"),
                          headers=auth("officer-1")).status_code == 404
        history = client.app.state.store
        uncensored = [day["dispensed"] for day in client.get(
            url + "&days=90", headers=auth("officer-1")).json()["days"] if not day["stockout"]]
        assert dispensing_series(history, "phc-1", "metformin") == uncensored


def test_stock_list_returns_latest_per_drug_and_enforces_facility_scope():
    with fresh_client() as client:
        path = "/api/v1/stock?facility_id=phc-1"
        before = client.get(path, headers=auth("pharmacist-1"))
        assert before.status_code == 200
        assert len(before.json()) == 4
        assert next(row for row in before.json() if row["drug_id"] == "metformin")["on_hand"] == 0
        assert all({"facility_id", "drug_id", "on_hand", "batches", "recorded_at",
                    "recorded_by", "source"} <= set(row) for row in before.json())
        updated = client.post("/api/v1/stock", headers=auth("pharmacist-1"), json={
            "drug_id": "metformin", "on_hand": 12,
            "batches": [{"id": "new-batch", "quantity": 12, "expiry_date": "2027-04-01"}],
        }).json()
        after = client.get(path, headers=auth("pharmacist-1")).json()
        assert len(after) == 4
        assert next(row for row in after if row["drug_id"] == "metformin")["id"] == updated["id"]
        assert client.get("/api/v1/stock", headers=auth("pharmacist-1")).status_code == 200
        assert client.get("/api/v1/stock?facility_id=phc-2",
                          headers=auth("pharmacist-1")).status_code == 403
        assert len(client.get(path, headers=auth("officer-1")).json()) == 4
        assert client.get(path, headers=auth("patient-user-001")).status_code == 403


def test_reference_and_demo_users_expose_bilingual_display_names():
    with fresh_client() as client:
        for path in ("/facilities", "/drugs", "/demo/users"):
            rows = client.get("/api/v1" + path, headers=auth("officer-1")).json()
            assert rows and all(row["name"] and row["name_hi"] for row in rows)
            assert all(row["synthetic_label"] == "Synthetic demo data" for row in rows)
        users = {row["id"]: row for row in client.get("/api/v1/demo/users").json()}
        for id, name, name_hi in (("asha-1", "Rekha", "रेखा"),
                                  ("pharmacist-1", "Sunita", "सुनीता"),
                                  ("officer-1", "Dr. Mehra", "डॉ. मेहरा")):
            assert (users[id]["name"], users[id]["name_hi"]) == (name, name_hi)
        patient = client.get("/api/v1/patients/patient-001",
                             headers=auth("patient-user-001")).json()
        assert patient["name_hi"] == "रमेश"
