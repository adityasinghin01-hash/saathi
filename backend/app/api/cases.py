from uuid import uuid4

from fastapi import APIRouter, Request

from app.api.shared import (
    LABEL,
    USER_DEP,
    ApiError,
    get_or_404,
    now,
    require_role,
    store_for,
)
from app.domain.ai import contains_medical_advice
from app.domain.status import transition

router = APIRouter()


def can_see_case(store, case: dict, user: dict) -> bool:
    if user["role"] == "district_officer":
        facility = store.get("facility", case["facility_id"])
        home = store.get("facility", user["facility_id"])
        return bool(facility and home and facility["district"] == home["district"])
    if user["role"] == "pharmacist":
        return case["facility_id"] == user["facility_id"]
    if user["role"] == "patient":
        return case["patient_id"] == user.get("patient_id")
    if user["role"] == "asha":
        patient = store.get("patient", case["patient_id"])
        return bool(patient and patient["asha_id"] == user["id"])
    return False


def visible_case(store, case_id: str, user: dict) -> dict:
    case = get_or_404(store, "case", case_id)
    if not can_see_case(store, case, user):
        raise ApiError(403, "forbidden", "Case is outside your scope")
    return case


def make_case(store, user: dict, body: dict) -> dict:
    require_role(user, "patient", "asha")
    missing = [name for name in ("patient_id", "drug_id", "requested_qty",
                               "household_supply_days", "attempted_at")
               if body.get(name) is None or body.get(name) == ""]
    if missing:
        raise ApiError(422, "validation_error", "Required case fields: " + ", ".join(missing))
    patient = get_or_404(store, "patient", str(body.get("patient_id", "")))
    if user["role"] == "patient" and patient["id"] != user.get("patient_id"):
        raise ApiError(403, "forbidden", "Patient is outside your scope")
    if user["role"] == "asha" and patient["asha_id"] != user["id"]:
        raise ApiError(403, "forbidden", "Patient is outside your scope")
    drug_id = str(body.get("drug_id", ""))
    get_or_404(store, "drug", drug_id)
    if not any(rx["patient_id"] == patient["id"] and rx["drug_id"] == drug_id and rx["active"]
               for rx in store.list("prescription")):
        raise ApiError(422, "invalid_drug", "Drug is not on an active prescription")
    try:
        quantity = int(body["requested_qty"])
        days = int(body["household_supply_days"])
    except (KeyError, ValueError, TypeError):
        raise ApiError(422, "validation_error", "Quantity and household supply days are required")
    if quantity <= 0 or days < 0 or body.get("channel", "manual") not in {"manual", "voice"}:
        raise ApiError(422, "validation_error", "Invalid case fields")
    attempted = body.get("attempted_at")
    if not isinstance(attempted, str) or not attempted.endswith("Z"):
        raise ApiError(422, "validation_error", "attempted_at must be UTC")
    transcript = body.get("transcript")
    if transcript is not None and not isinstance(transcript, str):
        raise ApiError(422, "validation_error", "Transcript must be text")
    if transcript and contains_medical_advice(transcript):
        raise ApiError(422, "medical_advice", "Medical advice text cannot be saved")
    stamp = now()
    case = {"id": f"case-{uuid4().hex}", "patient_id": patient["id"],
                "facility_id": patient["facility_id"], "drug_id": drug_id, "requested_qty": quantity,
                "received_qty": 0, "household_supply_days": days, "attempted_at": attempted,
                "reported_by": user["id"], "channel": body.get("channel", "manual"),
                "transcript": transcript, "status": "reported",
                "verification": {"result": None, "on_hand": None, "by": None, "at": None},
                "transfer_id": None, "created_at": stamp, "updated_at": stamp, "synthetic_label": LABEL}
    store.put("case", case)
    store.put("case_event", {"id": f"event-{uuid4().hex}", "case_id": case["id"],
                                  "from_status": None, "to_status": "reported", "actor_id": user["id"],
                                  "at": stamp, "note": "Case reported", "synthetic_label": LABEL})
    return case


@router.post("/cases")
def create_case(body: dict, request: Request, user: dict = USER_DEP):
    return make_case(store_for(request), user, body)


@router.get("/cases")
def list_cases(request: Request, status: str | None = None, facility_id: str | None = None,
               user: dict = USER_DEP):
    store = store_for(request)
    return [case for case in store.list("case") if can_see_case(store, case, user)
            and (status is None or case["status"] == status)
            and (facility_id is None or case["facility_id"] == facility_id)]


@router.get("/cases/{case_id}")
def case_detail(case_id: str, request: Request, user: dict = USER_DEP):
    store = store_for(request)
    case = visible_case(store, case_id, user)
    events = sorted((e for e in store.list("case_event") if e["case_id"] == case_id),
                    key=lambda event: event["at"])
    transfer = store.get("transfer", case["transfer_id"]) if case["transfer_id"] else None
    return {**case, "events": events, "transfer": transfer}


@router.post("/cases/{case_id}/verify")
def verify_case(case_id: str, body: dict, request: Request, user: dict = USER_DEP):
    require_role(user, "pharmacist")
    store = store_for(request)
    case = visible_case(store, case_id, user)
    if case["status"] != "reported":
        raise ApiError(409, "illegal_transition", "Case is not reported")
    result = body.get("result")
    try:
        on_hand = int(body["on_hand"])
    except (KeyError, ValueError, TypeError):
        raise ApiError(422, "validation_error", "on_hand is required")
    if result not in {"confirmed_stockout", "stock_available", "household_only"} or on_hand < 0:
        raise ApiError(422, "validation_error", "Invalid verification")
    if result == "confirmed_stockout" and on_hand != 0:
        raise ApiError(422, "validation_error", "Confirmed stockout requires zero on hand")
    stamp = now()
    case["verification"] = {"result": result, "on_hand": on_hand, "by": user["id"], "at": stamp}
    store.put("case", case)
    case = transition(store, case, "verified", user["id"], stamp, result)
    if result == "household_only":
        case = transition(store, case, "closed", user["id"], now(), "Household-only issue")
    return case


@router.post("/cases/{case_id}/supply")
def supply_case(case_id: str, body: dict, request: Request, user: dict = USER_DEP):
    require_role(user, "pharmacist")
    store = store_for(request)
    case = visible_case(store, case_id, user)
    try:
        quantity = int(body["quantity"])
    except (KeyError, ValueError, TypeError):
        raise ApiError(422, "validation_error", "quantity is required")
    if quantity <= 0:
        raise ApiError(422, "validation_error", "quantity must be positive")
    if case["received_qty"] + quantity > case["requested_qty"]:
        raise ApiError(422, "validation_error", "Supply exceeds requested quantity")
    if case["status"] not in {"received", "verified", "partially_supplied"} or (case["status"] == "verified" and
       case["verification"]["result"] != "stock_available"):
        raise ApiError(409, "illegal_transition", "Case cannot be supplied yet")
    from app.domain.forecast import latest_snapshot

    snapshot = latest_snapshot(store, case["facility_id"], case["drug_id"])
    if snapshot is None or snapshot["on_hand"] < quantity:
        raise ApiError(409, "insufficient_stock", "Insufficient recorded stock")
    batches = [dict(batch) for batch in sorted(snapshot["batches"],
                                               key=lambda row: (row["expiry_date"], row["id"]))]
    remaining = quantity
    for batch in batches:
        take = min(remaining, batch["quantity"])
        batch["quantity"] -= take
        remaining -= take
    if remaining:
        raise ApiError(409, "insufficient_stock", "Insufficient batch stock")
    stamp = now()
    store.put("stock_snapshot", {**snapshot, "id": f"stock-{uuid4().hex}",
                                 "on_hand": snapshot["on_hand"] - quantity,
                                 "batches": [batch for batch in batches if batch["quantity"] > 0],
                                 "recorded_at": stamp, "recorded_by": user["id"], "source": "manual"})
    store.put("dispensing", {"id": f"disp-{uuid4().hex}", "facility_id": case["facility_id"],
                                 "drug_id": case["drug_id"], "patient_id": case["patient_id"],
                                 "quantity": quantity, "dispensed_at": stamp, "synthetic_label": LABEL})
    case["received_qty"] += quantity
    store.put("case", case)
    target = "supplied" if case["received_qty"] >= case["requested_qty"] else "partially_supplied"
    return transition(store, case, target, user["id"], stamp, f"Supplied {quantity} unit(s)")


@router.post("/cases/{case_id}/confirm-received-by-patient")
def confirm_received(case_id: str, request: Request, user: dict = USER_DEP):
    require_role(user, "patient", "asha")
    store = store_for(request)
    case = visible_case(store, case_id, user)
    return transition(store, case, "closed", user["id"], now(), "Receipt confirmed")


@router.post("/cases/{case_id}/cancel")
def cancel_case(case_id: str, body: dict, request: Request, user: dict = USER_DEP):
    require_role(user, "patient", "asha", "pharmacist", "district_officer")
    store = store_for(request)
    case = visible_case(store, case_id, user)
    note = body.get("note")
    if not isinstance(note, str) or not note.strip():
        raise ApiError(422, "validation_error", "Cancellation note is required")
    if case["status"] in {"closed", "cancelled"}:
        raise ApiError(409, "illegal_transition", "Case transition is not allowed")
    if case["transfer_id"]:
        transfer = store.get("transfer", case["transfer_id"])
        if transfer and transfer["status"] in {"draft", "approved"}:
            store.put("transfer", {**transfer, "status": "cancelled"})
    return transition(store, case, "cancelled", user["id"], now(), note.strip())
