"""Independent patient-level demand simulator for forecast evaluation."""

import json
import math
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from app.domain.forecast import (
    calibrated_cohort_need,
    cohort_need,
    dispensing_forecast,
    forecast_components,
)

LABEL = "Synthetic demo data"
SCENARIOS = ("baseline", "enrolment_gap", "stale_prescriptions", "false_reports",
             "outside_purchases", "long_stockout")


class MemoryStore:
    def __init__(self):
        self.rows = {}

    def put(self, kind, row):
        self.rows.setdefault(kind, []).append(row)

    def list(self, kind):
        return self.rows.get(kind, [])


@dataclass
class Scenario:
    store: MemoryStore
    historical_demand: list[int]
    future_demand: list[int]
    future_clinic_requests: list[int]
    initial_stock: int
    population: int
    false_report_count: int


def build_scenario(name: str, repetition: int) -> Scenario:
    """Draw actual patient requests before making incomplete observation records."""
    if name not in SCENARIOS:
        raise ValueError(name)
    # Pair false-report runs with baseline demand and stock so only reports differ.
    scenario_index = 0 if name == "false_reports" else SCENARIOS.index(name)
    rng = random.Random(7301 + scenario_index * 1009 + repetition)
    store = MemoryStore()
    population = 80
    enrolled_count = 48 if name == "enrolment_gap" else 76
    enrolled_ids = set(rng.sample(range(population), enrolled_count))
    need = [0] * 120
    clinic_requests = [0] * 120
    patient_requests = [[] for _ in range(120)]
    for patient in range(population):
        enrolled = patient in enrolled_ids
        propensity = rng.uniform(0.48, 0.95)
        outside_chance = rng.uniform(0, 0.96 if name == "outside_purchases" else 0.16)
        if enrolled:
            patient_id = f"p-{patient}"
            store.put("patient", {"id": patient_id, "facility_id": "phc-eval"})
            store.put("prescription", {"id": f"rx-{patient}", "patient_id": patient_id,
                                       "drug_id": "metformin", "dose_per_day": 1,
                                       "active": True, "confirmed_by_staff": True})
        lapse = 0
        for day in range(120):
            if lapse:
                lapse -= 1
            elif rng.random() < 0.018:
                lapse = rng.randint(2, 7)
            elif rng.random() < propensity:
                need[day] += 1
                if rng.random() >= outside_chance:
                    clinic_requests[day] += 1
                    patient_requests[day].append(f"p-{patient}" if enrolled else f"u-{patient}")
    if name == "stale_prescriptions":
        for patient in range(35):
            patient_id = f"stale-{patient}"
            store.put("patient", {"id": patient_id, "facility_id": "phc-eval"})
            store.put("prescription", {"id": f"stale-rx-{patient}", "patient_id": patient_id,
                                       "drug_id": "metformin", "dose_per_day": 1,
                                       "active": True, "confirmed_by_staff": True})
    anchor = date(2026, 5, 1)
    for day, requests in enumerate(patient_requests[:90]):
        stockout = 32 <= day <= 36 or (name == "long_stockout" and day >= 50)
        stamp = (anchor + timedelta(days=day)).isoformat()
        if stockout:
            store.put("stockout_day", {"id": f"out-{day}", "facility_id": "phc-eval",
                                       "drug_id": "metformin", "date": stamp})
        for patient_id in ([] if stockout else requests):
            store.put("dispensing", {"id": f"disp-{day}-{patient_id}",
                                     "facility_id": "phc-eval", "drug_id": "metformin",
                                     "patient_id": patient_id, "quantity": 1,
                                     "dispensed_at": f"{stamp}T12:00:00Z"})
    stock = rng.randint(250, 850)
    false_reports = rng.randint(25, 45) if name == "false_reports" else 0
    for report in range(false_reports):
        store.put("false_report", {"id": f"false-{report}", "day": rng.randrange(90),
                                   "patient_id": f"p-{rng.randrange(population)}",
                                   "claimed_stockout": True, "stock_available": True})
    return Scenario(store, need[:90], need[90:], clinic_requests[90:],
                    stock, population, false_reports)


def simulate_supply(demand: list[int], initial_stock: int, forecast: float, alert: bool,
                    delivery_delay: int = 7) -> int:
    return simulate_supply_metrics(demand, initial_stock, forecast, alert, delivery_delay)[0]


def simulate_supply_metrics(demand: list[int], initial_stock: int, forecast: float, alert: bool,
                            delivery_delay: int = 7,
                            true_need_30: int | None = None) -> tuple[int, float, int]:
    stock = initial_stock
    delivery = max(0, math.ceil(forecast * 1.3) - initial_stock) if alert else 0
    unmet = 0
    overstock = 0
    stockout_days = 0
    thirty_day_need = sum(demand) if true_need_30 is None else true_need_30
    for day, requested in enumerate(demand):
        if day == delivery_delay:
            stock += delivery
        filled = min(stock, requested)
        stock -= filled
        unmet += requested - filled
        overstock += max(0, stock - thirty_day_need)
        stockout_days += int(stock == 0)
    return unmet, overstock / len(demand), stockout_days


def tune_prior_days() -> dict:
    """Choose prior strength on disjoint repetition IDs, never evaluation IDs."""
    candidates = (0, 10, 30, 60)
    errors = {candidate: 0.0 for candidate in candidates}
    for name in SCENARIOS:
        for repetition in range(1000, 1008):
            scenario = build_scenario(name, repetition)
            truth = sum(scenario.future_demand)
            for candidate in candidates:
                forecast = calibrated_cohort_need(scenario.store, "phc-eval", "metformin", 30,
                                                  candidate)
                errors[candidate] += abs(forecast - truth)
    selected = min(candidates, key=lambda candidate: (errors[candidate], candidate))
    return {"candidate_days": list(candidates), "training_repetitions": list(range(1000, 1008)),
            "selected_days": selected,
            "training_mae_daily": {str(k): round(v / (len(SCENARIOS) * 8 * 30), 2)
                                   for k, v in errors.items()}}


def evaluate(repetitions: int = 12) -> dict:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    tuning = tune_prior_days()
    output = {"label": LABEL, "seed": 7301, "history_days": 90, "horizon_days": 30,
              "repetitions": repetitions, "scenarios": {},
              "tuning": tuning,
              "methodology": {"truth": "Individual medicine need before outside purchases",
                              "false_alert": "Alert with enough stock for 14 days of PHC requests",
                              "unmet": "Unfilled PHC request patient-days; alert order arrives day 7",
                              "lead": "Cutoff alert days before true stockout; missed alert scores zero",
                              "overstock": "Mean daily on-hand units above true 30-day patient need",
                              "stockout_days": "Days ending with zero on-hand units"}}
    for name in SCENARIOS:
        measures = {key: {"errors": [], "false": 0, "alerts": 0, "unmet": [], "lead": [],
                          "overstock": [], "stockout_days": [], "shortages": 0}
                    for key in ("dispensing_only", "prescription_only", "calibrated", "combined")}
        reports = 0
        for repetition in range(repetitions):
            scenario = build_scenario(name, repetition)
            reports += scenario.false_report_count
            cohort = cohort_need(scenario.store, "phc-eval", "metformin", 30)
            dispensing = dispensing_forecast(scenario.store, "phc-eval", "metformin", 30)
            components = forecast_components(scenario.store, "phc-eval", "metformin", 30,
                                             tuning["selected_days"])
            estimates = {"dispensing_only": dispensing, "prescription_only": cohort,
                         "calibrated": components["calibrated_cohort_need"],
                         "combined": components["calibrated_combined"]}
            truth = sum(scenario.future_demand)
            cumulative = 0
            shortage_day = None
            for day, demand in enumerate(scenario.future_clinic_requests, 1):
                cumulative += demand
                if cumulative > scenario.initial_stock:
                    shortage_day = day
                    break
            true_14_shortage = (sum(scenario.future_clinic_requests[:14])
                                > scenario.initial_stock)
            for method, estimate in estimates.items():
                row = measures[method]
                alert = scenario.initial_stock / max(estimate / 30, 1e-6) < 14
                row["errors"].append(abs(estimate - truth) / 30)
                row["false"] += int(alert and not true_14_shortage)
                row["alerts"] += int(alert)
                unmet, overstock, stockout_days = simulate_supply_metrics(
                    scenario.future_clinic_requests, scenario.initial_stock, estimate, alert,
                    true_need_30=truth)
                row["unmet"].append(unmet)
                row["overstock"].append(overstock)
                row["stockout_days"].append(stockout_days)
                if shortage_day is not None:
                    row["shortages"] += 1
                    row["lead"].append(shortage_day if alert else 0)
        output["scenarios"][name] = {"false_report_count": reports, "methods": {
            method: {"mae_daily": round(sum(row["errors"]) / repetitions, 2),
                     "false_alert_rate": round(row["false"] / repetitions, 3),
                     "alerts": row["alerts"],
                     "unmet_patient_days": round(sum(row["unmet"]) / repetitions, 2),
                     "overstock_units": round(sum(row["overstock"]) / repetitions, 2),
                     "stockout_days": round(sum(row["stockout_days"]) / repetitions, 2),
                     "alert_lead_days": round(sum(row["lead"]) / len(row["lead"]), 2)
                     if row["lead"] else 0.0,
                     "real_shortages": row["shortages"]}
            for method, row in measures.items()}}
    return output


def write_results(result: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "forecast.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# Forecast evaluation", "", LABEL + ". Patient-level need is generated "
             "independently of all four forecast methods.", "",
             ("MAE is units/day against all patient need, including outside purchases. "
              "False alerts and unmet patient-days use PHC requests, excluding purchases "
              "filled elsewhere. False-alert rate uses all runs; other measures are means "
              "per run. A replenishment order takes seven days and is sized to 130% of "
             "the forecast."), "",
             (f"PDC prior days: {result['tuning']['selected_days']}, selected on repetitions "
              "1000–1007; scored repetitions begin at 0."), "",
             "| Scenario | Method | MAE/day | False alert rate | Unmet patient-days | Lead days | Overstock units | Stockout days |",
             "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, scenario in result["scenarios"].items():
        for method, row in scenario["methods"].items():
            lines.append(f"| {name} | {method} | {row['mae_daily']:.2f} | "
                         f"{row['false_alert_rate']:.3f} | {row['unmet_patient_days']:.2f} | "
                         f"{row['alert_lead_days']:.2f} | {row['overstock_units']:.2f} | "
                         f"{row['stockout_days']:.2f} |")
    losses = []
    for name, scenario in result["scenarios"].items():
        methods = scenario["methods"]
        combined = methods["combined"]
        for metric in ("mae_daily", "false_alert_rate", "unmet_patient_days",
                       "overstock_units", "stockout_days"):
            best_value = min(row[metric] for row in methods.values())
            winners = ", ".join(method for method, row in methods.items()
                                if row[metric] == best_value)
            losses.append(f"- {name}, {metric}: best {winners} ({best_value}); "
                          f"combined {combined[metric]}.")
    lines += ["", "## Measured wins and losses", "", *losses, "",
              ("False reports are generated separately. All four methods ignore case reports, "
               "so this stressor does not change their input data."), ""]
    (directory / "forecast.md").write_text("\n".join(lines))


if __name__ == "__main__":
    write_results(evaluate(), Path(__file__).parent / "results")
