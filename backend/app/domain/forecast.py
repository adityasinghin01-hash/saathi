import os
from datetime import date, timedelta

HORIZON_DAYS = 30
EPSILON = 1e-6
PDC_PRIOR_DAYS = 60


def cohort_need(store, facility_id: str, drug_id: str, horizon_days: int) -> int:
    patient_ids = {p["id"] for p in store.list("patient") if p["facility_id"] == facility_id}
    return sum(rx["dose_per_day"] * horizon_days for rx in store.list("prescription")
               if rx["patient_id"] in patient_ids and rx["drug_id"] == drug_id
               and rx["active"] and rx["confirmed_by_staff"])


def dispensing_series(store, facility_id: str, drug_id: str) -> list[int]:
    censored = _stockout_dates(store, facility_id, drug_id)
    daily = {}
    for row in store.list("dispensing"):
        day = row["dispensed_at"][:10]
        if row["facility_id"] == facility_id and row["drug_id"] == drug_id and day not in censored:
            daily[day] = daily.get(day, 0) + row["quantity"]
    # ASSUMPTION: omit censored days from the model series; never treat a stock-out as zero demand.
    return [daily[day] for day in sorted(daily)]


def _forecast(observations: list[int], horizon_days: int) -> float:
    import numpy as np
    from statsforecast.models import TSB

    if not observations:
        return 0.0
    series = np.asarray(observations, dtype=float)
    return float(TSB(alpha_d=0.2, alpha_p=0.2).forecast(series, h=horizon_days)["mean"].sum())


def dispensing_forecast(store, facility_id: str, drug_id: str, horizon_days: int) -> float:
    return _forecast(dispensing_series(store, facility_id, drug_id), horizon_days)


def _eligible_prescriptions(store, facility_id: str, drug_id: str) -> list[dict]:
    patient_ids = {p["id"] for p in store.list("patient") if p["facility_id"] == facility_id}
    return [rx for rx in store.list("prescription") if rx["patient_id"] in patient_ids
            and rx["drug_id"] == drug_id and rx["active"] and rx["confirmed_by_staff"]]


def _history(store, facility_id: str, drug_id: str):
    rows = [row for row in store.list("dispensing") if row["facility_id"] == facility_id
            and row["drug_id"] == drug_id]
    if not rows:
        return [], []
    censored = {date.fromisoformat(day) for day in _stockout_dates(store, facility_id, drug_id)}
    first = min(date.fromisoformat(row["dispensed_at"][:10]) for row in rows)
    last = max(date.fromisoformat(row["dispensed_at"][:10]) for row in rows)
    days = [first + timedelta(days=offset) for offset in range((last - first).days + 1)
            if first + timedelta(days=offset) not in censored]
    return days, [row for row in rows if date.fromisoformat(row["dispensed_at"][:10]) not in censored]


def calibrated_cohort_need(store, facility_id: str, drug_id: str, horizon_days: int,
                           prior_days: float = PDC_PRIOR_DAYS) -> float:
    """Shrink patient covered-day fractions toward the facility's observed PDC."""
    prescriptions = _eligible_prescriptions(store, facility_id, drug_id)
    if not prescriptions:
        return 0.0
    days, rows = _history(store, facility_id, drug_id)
    doses = {}
    for rx in prescriptions:
        doses[rx["patient_id"]] = doses.get(rx["patient_id"], 0) + rx["dose_per_day"]
    fills = {}
    for row in rows:
        if row.get("patient_id") in doses:
            key = (row["patient_id"], date.fromisoformat(row["dispensed_at"][:10]))
            fills[key] = fills.get(key, 0) + row["quantity"]
    covered = {}
    observed_days = {}
    for patient_id, daily_dose in doses.items():
        patient_fills = [day for pid, day in fills if pid == patient_id]
        patient_days = [day for day in days if patient_fills and day >= min(patient_fills)]
        balance = 0
        count = 0.0
        for day in patient_days:
            balance += fills.get((patient_id, day), 0)
            used = min(balance, daily_dose)
            count += used / daily_dose
            balance -= used
        covered[patient_id] = count
        observed_days[patient_id] = len(patient_days)
    total_days = sum(observed_days.values())
    facility_pdc = sum(covered.values()) / total_days if total_days else 1.0
    return sum(dose * horizon_days * ((covered[patient_id] + prior_days * facility_pdc)
               / (observed_days[patient_id] + prior_days)
               if observed_days[patient_id] + prior_days else facility_pdc)
               for patient_id, dose in doses.items())


def forecast_components(store, facility_id: str, drug_id: str, horizon_days: int,
                        prior_days: float = PDC_PRIOR_DAYS) -> dict[str, float]:
    """Return additive demand parts using only attributable unenrolled fills as residual."""
    prescriptions = _eligible_prescriptions(store, facility_id, drug_id)
    enrolled = {rx["patient_id"] for rx in prescriptions}
    days, rows = _history(store, facility_id, drug_id)
    daily = {day: 0 for day in days}
    for row in rows:
        patient_id = row.get("patient_id")
        day = date.fromisoformat(row["dispensed_at"][:10])
        if patient_id is not None and patient_id not in enrolled and day in daily:
            daily[day] += row["quantity"]
    residual = max(0.0, _forecast([daily[day] for day in days], horizon_days))
    calibrated = calibrated_cohort_need(store, facility_id, drug_id, horizon_days, prior_days)
    return {"calibrated_cohort_need": calibrated,
            "unenrolled_dispensing_forecast": residual,
            "calibrated_combined": calibrated + residual}


def demand_rule() -> str:
    rule = os.getenv("DEMAND_RULE", "max")
    if rule not in {"max", "calibrated"}:
        raise ValueError("DEMAND_RULE must be max or calibrated")
    return rule


def warning_level(days_left: float) -> str | None:
    if days_left < 7:
        return "critical"
    if days_left < 14:
        return "low"
    return None


def combined_estimate(cohort: float, dispensing: float, demand_rule: str = "max") -> float:
    if demand_rule == "dispensing_only":
        return dispensing
    return max(cohort, dispensing)


def latest_snapshot(store, facility_id: str, drug_id: str) -> dict | None:
    rows = [row for row in store.list("stock_snapshot")
            if row["facility_id"] == facility_id and row["drug_id"] == drug_id]
    return max(rows, key=lambda row: row["recorded_at"], default=None)


def _stockout_dates(store, facility_id: str, drug_id: str) -> set[str]:
    historical = {row["date"]: row["on_hand"] for row in store.list("daily_stock")
                  if row["facility_id"] == facility_id and row["drug_id"] == drug_id}
    legacy = {row["date"] for row in store.list("stockout_day")
              if row["facility_id"] == facility_id and row["drug_id"] == drug_id
              and row["date"] not in historical}
    return {day for day, on_hand in historical.items() if on_hand == 0} | legacy


def stock_history(store, facility_id: str, drug_id: str) -> list[dict]:
    """Daily graph points from the same stock and dispensing records used by the forecast."""
    daily = {row["date"]: row["on_hand"] for row in store.list("daily_stock")
             if row["facility_id"] == facility_id and row["drug_id"] == drug_id}
    dispensed = {}
    for row in store.list("dispensing"):
        if row["facility_id"] == facility_id and row["drug_id"] == drug_id:
            day = row["dispensed_at"][:10]
            dispensed[day] = dispensed.get(day, 0) + row["quantity"]
    return [{"date": day, "on_hand": daily[day], "dispensed": dispensed.get(day, 0),
             "stockout": daily[day] == 0}
            for day in sorted(daily)]


def daily_combined(store, facility_id: str, drug_id: str) -> float:
    if demand_rule() == "calibrated":
        return forecast_components(store, facility_id, drug_id, HORIZON_DAYS)[
            "calibrated_combined"] / HORIZON_DAYS
    cohort = cohort_need(store, facility_id, drug_id, HORIZON_DAYS)
    dispensing = dispensing_forecast(store, facility_id, drug_id, HORIZON_DAYS)
    drug = store.get("drug", drug_id)
    return combined_estimate(cohort, dispensing, drug.get("demand_rule", "max")) / HORIZON_DAYS
