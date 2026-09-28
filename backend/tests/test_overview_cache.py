import pytest
from fastapi.testclient import TestClient

from app.api import stock
from app.domain.ai import DeterministicFakeAI
from app.main import create_app
from app.storage.sqlite import SQLiteStore
from tests.conftest import auth

OVERVIEW = "/api/v1/district/overview?district=Suryanagar"


def selected_row(rows):
    return next(row for row in rows
                if row["facility_id"] == "phc-1" and row["drug_id"] == "metformin")


def test_overview_reuses_rows_and_stock_post_invalidates_cache(monkeypatch):
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
        assert calls == 28

        posted = client.post("/api/v1/stock", headers=auth("pharmacist-1"), json={
            "drug_id": "metformin", "on_hand": 19,
            "batches": [{"id": "cache-stock", "quantity": 19, "expiry_date": "2027-03-01"}],
        })
        assert posted.status_code == 200
        updated = client.get(OVERVIEW, headers=auth("officer-1"))
        assert updated.status_code == 200
        assert selected_row(updated.json())["on_hand"] == 19
        assert calls == 56


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


@pytest.mark.parametrize("kind", [
    "facility", "drug", "patient", "prescription", "stock_snapshot", "daily_stock",
    "stockout_day", "dispensing", "case", "transfer",
])
def test_overview_cache_invalidates_on_source_write(kind):
    store = SQLiteStore("sqlite:///:memory:")
    calls = 0

    def compute():
        nonlocal calls
        calls += 1
        return [{"revision": calls}]

    key = ("Suryanagar", 30, "max")
    assert store.cached_overview(key, compute) == [{"revision": 1}]
    assert store.cached_overview(key, compute) == [{"revision": 1}]
    store.put(kind, {"id": "changed"})
    assert store.cached_overview(key, compute) == [{"revision": 2}]
