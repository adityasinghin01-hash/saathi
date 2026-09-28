from app.domain.forecast import (
    calibrated_cohort_need,
    cohort_need,
    dispensing_series,
    forecast_components,
    warning_level,
)
from tests.test_seed import MemoryStore


def test_cohort_excludes_unconfirmed_and_inactive_prescriptions():
    store = MemoryStore()
    store.put("patient", {"id": "p1", "facility_id": "f1"})
    store.put("patient", {"id": "p2", "facility_id": "f2"})
    for id, patient_id, dose, active, confirmed in [
        ("a", "p1", 2, True, True), ("b", "p1", 3, False, True),
        ("c", "p1", 4, True, False), ("d", "p2", 8, True, True),
    ]:
        store.put("prescription", {"id": id, "patient_id": patient_id, "drug_id": "d1",
                                       "dose_per_day": dose, "active": active,
                                       "confirmed_by_staff": confirmed})
    assert cohort_need(store, "f1", "d1", 30) == 60


def test_warning_boundaries():
    assert warning_level(6.99) == "critical"
    assert warning_level(7) == "low"
    assert warning_level(14) is None


def test_stockout_days_are_censored_not_zero_demand():
    store = MemoryStore()
    for day, quantity in [("2026-09-01", 2), ("2026-09-02", 0), ("2026-09-03", 3)]:
        store.put("dispensing", {"id": day, "facility_id": "f1", "drug_id": "d1",
                                 "quantity": quantity, "dispensed_at": f"{day}T12:00:00Z"})
    store.put("stockout_day", {"id": "out", "facility_id": "f1", "drug_id": "d1",
                               "date": "2026-09-02"})
    store.put("dispensing", {"id": "extra", "facility_id": "f1", "drug_id": "d1",
                             "quantity": 4, "dispensed_at": "2026-09-03T15:00:00Z"})
    assert dispensing_series(store, "f1", "d1") == [2, 7]


def test_daily_on_hand_is_authoritative_for_stockout_censoring():
    store = MemoryStore()
    store.put("dispensing", {"id": "one", "facility_id": "f1", "drug_id": "d1",
                             "quantity": 2, "dispensed_at": "2026-09-01T12:00:00Z"})
    store.put("stockout_day", {"id": "legacy", "facility_id": "f1", "drug_id": "d1",
                               "date": "2026-09-01"})
    store.put("daily_stock", {"id": "stock", "facility_id": "f1", "drug_id": "d1",
                              "date": "2026-09-01", "on_hand": 5})
    assert dispensing_series(store, "f1", "d1") == [2]


def test_calibration_shrinks_sparse_patient_toward_facility_pdc():
    store = MemoryStore()
    for patient_id in ("regular", "sparse"):
        store.put("patient", {"id": patient_id, "facility_id": "f1"})
        store.put("prescription", {"id": patient_id, "patient_id": patient_id,
                                   "drug_id": "d1", "dose_per_day": 1,
                                   "active": True, "confirmed_by_staff": True})
    for day in range(1, 11):
        stamp = f"2026-09-{day:02d}T12:00:00Z"
        store.put("dispensing", {"id": f"r-{day}", "facility_id": "f1", "drug_id": "d1",
                                 "patient_id": "regular", "quantity": 1, "dispensed_at": stamp})
    store.put("dispensing", {"id": "s-1", "facility_id": "f1", "drug_id": "d1",
                             "patient_id": "sparse", "quantity": 1,
                             "dispensed_at": "2026-09-01T12:00:00Z"})
    # Facility PDC is 11 / 20; regular is 10 / 10; sparse is 1 / 10.
    assert calibrated_cohort_need(store, "f1", "d1", 10, prior_days=10) == 11


def test_combined_residual_excludes_enrolled_and_anonymous_dispensing():
    store = MemoryStore()
    store.put("patient", {"id": "p1", "facility_id": "f1"})
    store.put("prescription", {"id": "rx1", "patient_id": "p1", "drug_id": "d1",
                               "dose_per_day": 1, "active": True, "confirmed_by_staff": True})
    for day in range(1, 11):
        stamp = f"2026-09-{day:02d}T12:00:00Z"
        for patient_id, qty in (("p1", 1), ("u1", 2), (None, 5)):
            store.put("dispensing", {"id": f"{patient_id}-{day}", "facility_id": "f1",
                                     "drug_id": "d1", "patient_id": patient_id,
                                     "quantity": qty, "dispensed_at": stamp})
    components = forecast_components(store, "f1", "d1", 10, prior_days=10)
    assert components["calibrated_cohort_need"] == 10
    assert components["unenrolled_dispensing_forecast"] == 20
    assert components["calibrated_combined"] == 30
