import math
from datetime import date

from app.domain.forecast import daily_combined, latest_snapshot, warning_level
from app.domain.transfers import select_donor
from app.seed.data import seed_if_empty


class MemoryStore:
    def __init__(self):
        self.rows = {}

    def get(self, kind, id):
        return self.rows.get((kind, id))

    def list(self, kind):
        return [value for (row_kind, _), value in self.rows.items() if row_kind == kind]

    def put(self, kind, item):
        self.rows[(kind, item["id"])] = item


def test_seed_is_deterministic_and_idempotent():
    first = MemoryStore()
    second = MemoryStore()
    seed_if_empty(first)
    seed_if_empty(second)
    assert first.rows == second.rows
    assert len(first.list("facility")) == 7
    assert len(first.list("patient")) == 60
    assert len(first.list("drug")) == 4
    assert len(first.list("stockout_day")) >= 10
    assert all("Synthetic demo data" == row["synthetic_label"] for row in first.rows.values())
    seed_if_empty(first)
    assert first.rows == second.rows


def test_patient_roster_has_varied_names_ages_and_matching_demo_users():
    store = MemoryStore()
    seed_if_empty(store)
    patients = store.list("patient")
    by_id = {row["id"]: row for row in patients}
    assert (by_id["patient-001"]["name"], by_id["patient-001"]["name_hi"],
            by_id["patient-001"]["age"]) == ("Ramesh", "रमेश", 54)
    assert (by_id["patient-002"]["name"], by_id["patient-002"]["name_hi"],
            by_id["patient-002"]["sex"]) == ("Shabana Khan", "शबाना ख़ान", "F")
    assert (by_id["patient-004"]["name"], by_id["patient-004"]["name_hi"],
            by_id["patient-004"]["sex"]) == ("Iqbal Ansari", "इक़बाल अंसारी", "M")
    assert len({row["name"] for row in patients}) == 60
    assert len({row["name"].split()[0] for row in patients}) >= 45
    assert len({row["name"].split()[-1] for row in patients}) >= 15
    assert len({row["age"] for row in patients}) >= 25
    assert all(35 <= row["age"] <= 75 for row in patients)
    assert all(row["name_hi"] and all("\u0900" <= char <= "\u097f" or char == " "
                                      for char in row["name_hi"]) for row in patients)
    for asha_id in ("asha-1", "asha-2"):
        assigned = [row for row in patients if row["asha_id"] == asha_id]
        assert len(assigned) == 30
        assert {row["sex"] for row in assigned} == {"F", "M"}
        assert len({row["name"].split()[-1] for row in assigned}) >= 12
    for patient in patients:
        user = store.get("user", f"patient-user-{patient['id'][-3:]}")
        assert (user["name"], user["name_hi"], user["patient_id"]) == (
            patient["name"], patient["name_hi"], patient["id"])


def test_ramesh_has_exactly_one_feasible_metformin_donor():
    store = MemoryStore()
    seed_if_empty(store)
    assert latest_snapshot(store, "phc-1", "metformin")["on_hand"] == 0
    assert latest_snapshot(store, "store-1", "metformin")["on_hand"] >= 500
    case = {"facility_id": "phc-1", "drug_id": "metformin", "requested_qty": 30}
    eligible = []
    for facility in store.list("facility"):
        if facility["type"] != "PHC" or facility["id"] == "phc-1":
            continue
        snapshot = latest_snapshot(store, facility["id"], "metformin")
        safety = math.ceil(14 * daily_combined(store, facility["id"], "metformin"))
        if snapshot["on_hand"] - safety >= 30 and any(
            batch["quantity"] >= 30 and batch["expiry_date"] > "2026-10-30"
            for batch in snapshot["batches"]
        ):
            eligible.append(facility["id"])
    assert eligible == ["phc-2"]
    assert select_donor(store, case, date(2026, 9, 29))["donor"]["id"] == "phc-2"


def test_metformin_stock_is_varied_without_another_feasible_phc_donor():
    store = MemoryStore()
    seed_if_empty(store)
    warnings = set()
    for facility_id in ("phc-3", "phc-4", "phc-5", "phc-6"):
        on_hand = latest_snapshot(store, facility_id, "metformin")["on_hand"]
        daily = daily_combined(store, facility_id, "metformin")
        safety = math.ceil(14 * daily)
        assert 0 < on_hand <= safety
        warnings.add(warning_level(on_hand / daily))
    assert warnings == {None, "low"}

    other_drug_warnings = [
        warning_level(latest_snapshot(store, facility["id"], drug_id)["on_hand"]
                      / daily_combined(store, facility["id"], drug_id))
        for facility in store.list("facility") if facility["type"] == "PHC"
        for drug_id in ("glimepiride", "amlodipine", "telmisartan")
    ]
    assert other_drug_warnings.count("low") >= 2
    assert other_drug_warnings.count(None) > other_drug_warnings.count("low")
