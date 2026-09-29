from fastapi.testclient import TestClient

from app.api import stock
from app.domain import forecast
from app.domain.ai import DeterministicFakeAI
from app.main import create_app
from tests.conftest import auth

OVERVIEW = "/api/v1/district/overview?district=Suryanagar"


def selected_row(rows):
    return next(row for row in rows
                if row["facility_id"] == "phc-1" and row["drug_id"] == "metformin")


def legacy_rows(store, horizon_days=30):
    return [stock.overview_row(store, facility, drug, horizon_days)
            for facility in store.list("facility") for drug in store.list("drug")]


def test_precomputed_overview_matches_legacy_before_and_after_ramesh_flow(monkeypatch):
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        store = client.app.state.store
        before = legacy_rows(store)
        original_forecast = stock.dispensing_forecast

        def unexpected_forecast(*args):
            raise AssertionError("overview recomputed historical dispensing")

        monkeypatch.setattr(stock, "dispensing_forecast", unexpected_forecast)
        response = client.get(OVERVIEW, headers=auth("officer-1"))
        assert response.status_code == 200
        assert response.json() == before

        case = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
            "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 30,
            "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z",
            "channel": "manual",
        }).json()
        case_id = case["id"]
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
                           headers=auth("patient-user-001")).status_code == 200

        monkeypatch.setattr(stock, "dispensing_forecast", original_forecast)
        after = legacy_rows(store)
        monkeypatch.setattr(stock, "dispensing_forecast", unexpected_forecast)
        response = client.get(OVERVIEW, headers=auth("officer-1"))
        assert response.status_code == 200
        assert response.json() == after
        assert selected_row(after)["dispensing_forecast"] != selected_row(before)[
            "dispensing_forecast"]


def test_other_horizons_and_calibrated_rule_match_legacy(monkeypatch):
    monkeypatch.setenv("DEMAND_RULE", "calibrated")
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        store = client.app.state.store
        for horizon_days in (7, 90):
            response = client.get(f"{OVERVIEW}&horizon_days={horizon_days}",
                                  headers=auth("officer-1"))
            assert response.status_code == 200
            assert response.json() == legacy_rows(store, horizon_days)


def test_new_dispensing_recomputes_only_affected_forecast(monkeypatch):
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        store = client.app.state.store
        original = forecast._forecast
        observations = []

        def counted(series, horizon_days):
            observations.append((series, horizon_days))
            return original(series, horizon_days)

        monkeypatch.setattr(forecast, "_forecast", counted)
        assert client.get(OVERVIEW, headers=auth("officer-1")).status_code == 200
        assert observations == []
        store.put("dispensing", {"id": "extra-dispensing", "facility_id": "phc-1",
                                 "drug_id": "metformin", "patient_id": "patient-001",
                                 "quantity": 30, "dispensed_at": "2026-09-29T12:00:00Z"})
        assert client.get(OVERVIEW, headers=auth("officer-1")).status_code == 200
        assert len(observations) == 2
        assert client.get(OVERVIEW, headers=auth("officer-1")).status_code == 200
        assert len(observations) == 2


def test_overview_rebuilds_current_rows_after_stock_post(monkeypatch):
    calls = 0
    original = stock.overview_row

    def counted(*args):
        nonlocal calls
        calls += 1
        return original(*args)

    monkeypatch.setattr(stock, "overview_row", counted)
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        first = client.get(OVERVIEW, headers=auth("officer-1"))
        assert first.status_code == 200
        assert calls == 28
        second = client.get(OVERVIEW, headers=auth("officer-1"))
        assert second.json() == first.json()
        assert calls == 56

        posted = client.post("/api/v1/stock", headers=auth("pharmacist-1"), json={
            "drug_id": "metformin", "on_hand": 19,
            "batches": [{"id": "cache-stock", "quantity": 19, "expiry_date": "2027-03-01"}],
        })
        assert posted.status_code == 200
        updated = client.get(OVERVIEW, headers=auth("officer-1"))
        assert updated.status_code == 200
        assert selected_row(updated.json())["on_hand"] == 19
        assert calls == 84


def test_case_changes_and_demo_reset_invalidate_overview(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as client:
        before = selected_row(client.get(OVERVIEW, headers=auth("officer-1")).json())
        case = client.post("/api/v1/cases", headers=auth("patient-user-001"), json={
            "patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 12,
            "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z",
        })
        assert case.status_code == 200
        opened = selected_row(client.get(OVERVIEW, headers=auth("officer-1")).json())
        assert opened["open_cases"] == before["open_cases"] + 1
        cancelled = client.post(f"/api/v1/cases/{case.json()['id']}/cancel",
                                headers=auth("patient-user-001"), json={"note": "Resolved"})
        assert cancelled.status_code == 200
        closed = selected_row(client.get(OVERVIEW, headers=auth("officer-1")).json())
        assert closed["open_cases"] == before["open_cases"]

        stock_post = client.post("/api/v1/stock", headers=auth("pharmacist-1"), json={
            "drug_id": "metformin", "on_hand": 19,
            "batches": [{"id": "cache-reset", "quantity": 19, "expiry_date": "2027-03-01"}],
        })
        assert stock_post.status_code == 200
        assert selected_row(client.get(OVERVIEW, headers=auth("officer-1")).json())[
            "on_hand"] == 19
        reset = client.post("/api/v1/demo/reset", headers=auth("officer-1"))
        assert reset.status_code == 200
        after = selected_row(client.get(OVERVIEW, headers=auth("officer-1")).json())
        assert after["on_hand"] == before["on_hand"]
        assert after["open_cases"] == before["open_cases"]
