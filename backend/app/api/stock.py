from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Query, Request

from app.api.shared import (
    LABEL,
    USER_DEP,
    ApiError,
    get_or_404,
    now,
    require_role,
    store_for,
)
from app.domain.forecast import (
    EPSILON,
    HORIZON_DAYS,
    cohort_need,
    combined_estimate,
    demand_rule,
    dispensing_forecast,
    forecast_components,
    latest_snapshot,
    stock_history,
    warning_level,
)

router = APIRouter()


def record_stock(store, user: dict, body: dict) -> dict:
    require_role(user, "pharmacist")
    drug_id = str(body.get("drug_id", ""))
    get_or_404(store, "drug", drug_id)
    try:
        on_hand = int(body["on_hand"])
        batches = body["batches"]
        total = sum(int(batch["quantity"]) for batch in batches)
    except (KeyError, TypeError, ValueError):
        raise ApiError(422, "validation_error", "Invalid stock quantities")
    if on_hand < 0 or total != on_hand or any(int(b["quantity"]) < 0 for b in batches):
        raise ApiError(422, "validation_error", "Batch quantities must equal on_hand")
    if body.get("source", "manual") != "manual":
        # ASSUMPTION: the demo pharmacist can record only manual snapshots.
        raise ApiError(422, "validation_error", "Only manual stock recording is available")
    for batch in batches:
        if not isinstance(batch.get("expiry_date"), str) or not isinstance(batch.get("id"), str):
            raise ApiError(422, "validation_error", "Batch id and expiry_date are required")
        try:
            date.fromisoformat(batch["expiry_date"])
        except ValueError:
            raise ApiError(422, "validation_error", "Batch expiry_date must be an ISO date")
    normalized = []
    for batch in batches:
        row = {"id": batch["id"], "facility_id": user["facility_id"], "drug_id": drug_id,
                   "quantity": int(batch["quantity"]), "expiry_date": batch["expiry_date"],
                   "synthetic_label": LABEL}
        store.put("batch", row)
        normalized.append(row)
    snapshot = {"id": f"stock-{uuid4().hex}", "facility_id": user["facility_id"], "drug_id": drug_id,
                    "on_hand": on_hand, "batches": normalized, "recorded_at": now(),
                    "recorded_by": user["id"], "source": "manual", "synthetic_label": LABEL}
    store.put("stock_snapshot", snapshot)
    return snapshot


@router.post("/stock")
def new_stock(body: dict, request: Request, user: dict = USER_DEP):
    return record_stock(store_for(request), user, body)


@router.get("/stock")
def list_stock(request: Request, facility_id: str | None = None, user: dict = USER_DEP):
    require_role(user, "pharmacist", "district_officer")
    store = store_for(request)
    home = get_or_404(store, "facility", user["facility_id"])
    if facility_id is not None:
        facility = get_or_404(store, "facility", facility_id)
        if (user["role"] == "pharmacist" and facility_id != user["facility_id"] or
                user["role"] == "district_officer" and facility["district"] != home["district"]):
            raise ApiError(403, "forbidden", "Facility is outside your scope")
    facility_ids = ([facility_id] if facility_id else
                    [user["facility_id"]] if user["role"] == "pharmacist" else
                    [facility["id"] for facility in store.list("facility")
                     if facility["district"] == home["district"]])
    rows = []
    for selected in sorted(facility_ids):
        for drug in sorted(store.list("drug"), key=lambda row: row["id"]):
            snapshot = latest_snapshot(store, selected, drug["id"])
            if snapshot is not None:
                rows.append(snapshot)
    return rows


def overview_row(store, facility: dict, drug: dict, horizon_days: int,
                 current: dict | None = None) -> dict:
    pair = (facility["id"], drug["id"])
    if current is None:
        snapshot = latest_snapshot(store, *pair)
        cohort = cohort_need(store, *pair, horizon_days)
        dispensing = dispensing_forecast(store, *pair, horizon_days)
        components = forecast_components(store, *pair, horizon_days)
        cases = [case for case in store.list("case") if case["facility_id"] == facility["id"]
                 and case["drug_id"] == drug["id"] and case["status"] not in {"closed", "cancelled"}]
        open_cases = len(cases)
    else:
        snapshot = current["snapshots"].get(pair)
        cohort, dispensing, components = current["forecasts"][pair]
        open_cases = current["open_cases"].get(pair, 0)
    rule = demand_rule()
    combined = (components["calibrated_combined"] if rule == "calibrated"
                else combined_estimate(cohort, dispensing, drug.get("demand_rule", "max")))
    on_hand = snapshot["on_hand"] if snapshot else 0
    days_left = on_hand / max(combined / horizon_days, EPSILON)
    return {"facility_id": facility["id"], "drug_id": drug["id"],
            "on_hand": on_hand, "recorded_at": snapshot["recorded_at"] if snapshot else None,
            "cohort_need": cohort, "dispensing_forecast": dispensing,
            "calibrated_cohort_need": components["calibrated_cohort_need"],
            "unenrolled_dispensing_forecast": components["unenrolled_dispensing_forecast"],
            "demand_rule": rule, "combined": combined, "horizon_days": horizon_days,
            "days_left": days_left, "warning": warning_level(days_left),
            "open_cases": open_cases, "synthetic_label": LABEL}


@router.get("/district/overview")
def district_overview(request: Request, district: str | None = None,
                      horizon_days: int = Query(default=HORIZON_DAYS, ge=7, le=90),
                      user: dict = USER_DEP):
    require_role(user, "district_officer")
    store = store_for(request)
    home = get_or_404(store, "facility", user["facility_id"])
    if district is not None and district != home["district"]:
        raise ApiError(403, "forbidden", "District is outside your scope")
    facilities = [facility for facility in store.list("facility")
                  if facility["district"] == home["district"]]
    drugs = store.list("drug")
    snapshots = {}
    for row in store.list("stock_snapshot"):
        pair = (row["facility_id"], row["drug_id"])
        if pair not in snapshots or row["recorded_at"] > snapshots[pair]["recorded_at"]:
            snapshots[pair] = row
    open_cases = {}
    for case in store.list("case"):
        if case["status"] not in {"closed", "cancelled"}:
            pair = (case["facility_id"], case["drug_id"])
            open_cases[pair] = open_cases.get(pair, 0) + 1
    pairs = [(facility["id"], drug["id"]) for facility in facilities for drug in drugs]
    current = {"snapshots": snapshots, "open_cases": open_cases,
               "forecasts": store.overview_forecasts(pairs, horizon_days)}
    return [overview_row(store, facility, drug, horizon_days, current)
            for facility in facilities for drug in drugs]


@router.get("/district/series")
def district_series(request: Request, facility_id: str, drug_id: str,
                    days: int = Query(default=60, ge=1, le=90), user: dict = USER_DEP):
    require_role(user, "district_officer")
    store = store_for(request)
    home = get_or_404(store, "facility", user["facility_id"])
    facility = get_or_404(store, "facility", facility_id)
    drug = get_or_404(store, "drug", drug_id)
    if facility["district"] != home["district"]:
        raise ApiError(403, "forbidden", "Facility is outside your scope")
    row = overview_row(store, facility, drug, HORIZON_DAYS)
    horizon = row["horizon_days"]
    return {"facility_id": facility_id, "drug_id": drug_id,
            "days": stock_history(store, facility_id, drug_id)[-days:],
            "cohort_need_daily": row["cohort_need"] / horizon,
            "dispensing_forecast_daily": row["dispensing_forecast"] / horizon,
            "combined_daily": row["combined"] / horizon,
            "days_left": row["days_left"], "horizon_days": horizon,
            "synthetic_label": LABEL}
