import math
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Request

from app.api.cases import visible_case
from app.api.shared import (
    LABEL,
    USER_DEP,
    ApiError,
    get_or_404,
    now,
    require_role,
    store_for,
)
from app.domain.ai import AIUnavailable, DeterministicFakeAI, UnsafeAIOutput
from app.domain.forecast import daily_combined, latest_snapshot
from app.domain.status import transition
from app.domain.transfers import select_donor

router = APIRouter()


def can_see_transfer(store, transfer: dict, user: dict) -> bool:
    if user["role"] == "pharmacist":
        return user["facility_id"] in {transfer["to_facility_id"],
                                       transfer["from_facility_id"]}
    if user["role"] == "district_officer":
        home = store.get("facility", user["facility_id"])
        receiver = store.get("facility", transfer["to_facility_id"])
        return bool(home and receiver and home["district"] == receiver["district"])
    return False


@router.get("/transfers")
def list_transfers(request: Request, status: str | None = None,
                   facility_id: str | None = None, user: dict = USER_DEP):
    require_role(user, "district_officer", "pharmacist")
    store = store_for(request)
    if facility_id is not None:
        facility = get_or_404(store, "facility", facility_id)
        home = get_or_404(store, "facility", user["facility_id"])
        if (user["role"] == "pharmacist" and facility_id != user["facility_id"] or
                user["role"] == "district_officer" and facility["district"] != home["district"]):
            raise ApiError(403, "forbidden", "Facility is outside your scope")
    rows = [transfer for transfer in store.list("transfer")
            if can_see_transfer(store, transfer, user)
            and (status is None or transfer["status"] == status)
            and (facility_id is None or facility_id in {transfer["from_facility_id"],
                                                         transfer["to_facility_id"]})]
    return sorted(rows, key=lambda transfer: (transfer["created_at"], transfer["id"]),
                  reverse=True)


@router.get("/transfers/{transfer_id}")
def transfer_detail(transfer_id: str, request: Request, user: dict = USER_DEP):
    require_role(user, "district_officer", "pharmacist")
    store = store_for(request)
    transfer = get_or_404(store, "transfer", transfer_id)
    if not can_see_transfer(store, transfer, user):
        raise ApiError(403, "forbidden", "Transfer is outside your scope")
    return transfer


def officer_transfer(store, transfer_id: str, user: dict) -> dict:
    require_role(user, "district_officer")
    transfer = get_or_404(store, "transfer", transfer_id)
    visible_case(store, transfer["case_id"], user)
    return transfer


@router.post("/transfers/draft")
def draft_transfer(body: dict, request: Request, user: dict = USER_DEP):
    require_role(user, "district_officer")
    store = store_for(request)
    case = visible_case(store, str(body.get("case_id", "")), user)
    if case["status"] != "verified" or case["verification"]["result"] != "confirmed_stockout":
        raise ApiError(409, "illegal_transition", "Case is not a verified stockout")
    choice = select_donor(store, case, datetime.now(UTC).date())
    if choice is None:
        case["escalated"] = True
        store.put("case", case)
        return {"case_id": case["id"], "status": "no_feasible_transfer",
                "reason": "needs_split_or_supply", "ai_source": "fallback",
                "synthetic_label": LABEL}
    try:
        rationale_draft = request.app.state.ai.transfer_rationale(
            case, choice["donor"], choice["distance_km"])
    except AIUnavailable:
        rationale_draft = DeterministicFakeAI().transfer_rationale(
            case, choice["donor"], choice["distance_km"])
        rationale_draft["ai_source"] = "fallback"
    except UnsafeAIOutput as exc:
        raise ApiError(422, "ai_output_rejected", "Transfer rationale needs manual review") from exc
    transfer = {"id": f"transfer-{uuid4().hex}", "case_id": case["id"], "drug_id": case["drug_id"],
                    "from_facility_id": choice["donor"]["id"], "to_facility_id": case["facility_id"],
                    "quantity": case["requested_qty"], "batch_ids": [b["batch_id"] for b in choice["batches"]],
                    "batch_allocations": choice["batches"], "status": "draft", "drafted_by": "agent",
                    **rationale_draft,
                    "constraints_checked": {"donor_safety_stock_ok": True, "expiry_ok": True, "units_ok": True},
                    "approved_by": None, "created_at": now(), "synthetic_label": LABEL}
    store.put("transfer", transfer)
    case["transfer_id"] = transfer["id"]
    store.put("case", case)
    transition(store, case, "transfer_drafted", user["id"], now(), "Transfer drafted for review")
    return transfer


@router.post("/transfers/{transfer_id}/approve")
def approve_transfer(transfer_id: str, request: Request, user: dict = USER_DEP):
    store = store_for(request)
    transfer = officer_transfer(store, transfer_id, user)
    if transfer["status"] != "draft":
        raise ApiError(409, "illegal_transition", "Transfer is not draft")
    case = get_or_404(store, "case", transfer["case_id"])
    if case["status"] != "transfer_drafted" or case["transfer_id"] != transfer_id:
        raise ApiError(409, "illegal_transition", "Case is not awaiting this transfer")
    transfer["status"] = "approved"
    transfer["approved_by"] = user["id"]
    store.put("transfer", transfer)
    transition(store, case, "transfer_approved", user["id"], now(), "Transfer approved")
    return transfer


@router.post("/transfers/{transfer_id}/reject")
def reject_transfer(transfer_id: str, request: Request, user: dict = USER_DEP):
    store = store_for(request)
    transfer = officer_transfer(store, transfer_id, user)
    if transfer["status"] != "draft":
        raise ApiError(409, "illegal_transition", "Transfer is not draft")
    transfer["status"] = "rejected"
    store.put("transfer", transfer)
    case = get_or_404(store, "case", transfer["case_id"])
    if case["status"] != "transfer_drafted" or case["transfer_id"] != transfer_id:
        raise ApiError(409, "illegal_transition", "Case is not awaiting this transfer")
    transition(store, case, "verified", user["id"], now(), "Transfer rejected")
    return transfer


def movement_snapshot(store, transfer: dict, facility_id: str, direction: int, actor_id: str):
    previous = latest_snapshot(store, facility_id, transfer["drug_id"])
    batches = [dict(b) for b in previous["batches"]]
    if direction < 0:
        allocations = {b["batch_id"]: b["quantity"] for b in transfer["batch_allocations"]}
        for batch in batches:
            batch["quantity"] -= allocations.get(batch["id"], 0)
        batches = [b for b in batches if b["quantity"] > 0]
    else:
        for allocation in transfer["batch_allocations"]:
            batches.append({"id": f"received-{transfer['id']}-{allocation['batch_id']}",
                                "facility_id": facility_id, "drug_id": transfer["drug_id"],
                                "quantity": allocation["quantity"],
                                "expiry_date": allocation["expiry_date"], "synthetic_label": LABEL})
    snapshot = {"id": f"stock-{uuid4().hex}", "facility_id": facility_id,
                    "drug_id": transfer["drug_id"], "on_hand": previous["on_hand"] + direction * transfer["quantity"],
                    "batches": batches, "recorded_at": now(), "recorded_by": actor_id,
                    "source": "manual", "synthetic_label": LABEL}
    store.put("stock_snapshot", snapshot)


@router.post("/transfers/{transfer_id}/dispatch")
def dispatch_transfer(transfer_id: str, request: Request, user: dict = USER_DEP):
    store = store_for(request)
    transfer = officer_transfer(store, transfer_id, user)
    if transfer["status"] != "approved":
        raise ApiError(409, "illegal_transition", "Transfer is not approved")
    case = get_or_404(store, "case", transfer["case_id"])
    if case["status"] != "transfer_approved":
        raise ApiError(409, "illegal_transition", "Case is not ready for dispatch")
    # ASSUMPTION: recheck donor stock at dispatch to avoid sending already used units.
    snapshot = latest_snapshot(store, transfer["from_facility_id"], transfer["drug_id"])
    amounts = {b["id"]: b["quantity"] for b in snapshot["batches"]}
    if any(amounts.get(a["batch_id"], 0) < a["quantity"] for a in transfer["batch_allocations"]):
        raise ApiError(409, "stock_changed", "Donor stock changed after draft")
    if any(date.fromisoformat(a["expiry_date"]) <= datetime.now(UTC).date() + timedelta(days=31)
           for a in transfer["batch_allocations"]):
        raise ApiError(409, "expiry_changed", "Allocated batch no longer meets expiry rule")
    safety = math.ceil(14 * daily_combined(store, transfer["from_facility_id"], transfer["drug_id"]))
    if snapshot["on_hand"] - transfer["quantity"] < safety:
        raise ApiError(409, "stock_changed", "Donor safety stock changed after draft")
    movement_snapshot(store, transfer, transfer["from_facility_id"], -1, user["id"])
    transfer["status"] = "dispatched"
    store.put("transfer", transfer)
    transition(store, case, "dispatched", user["id"], now(), "Transfer dispatched")
    return transfer


@router.post("/transfers/{transfer_id}/receive")
def receive_transfer(transfer_id: str, request: Request, user: dict = USER_DEP):
    require_role(user, "pharmacist")
    store = store_for(request)
    transfer = get_or_404(store, "transfer", transfer_id)
    if transfer["to_facility_id"] != user["facility_id"]:
        raise ApiError(403, "forbidden", "Transfer is outside your facility")
    if transfer["status"] != "dispatched":
        raise ApiError(409, "illegal_transition", "Transfer is not dispatched")
    case = get_or_404(store, "case", transfer["case_id"])
    if case["status"] not in {"dispatched", "cancelled"}:
        raise ApiError(409, "illegal_transition", "Case is not awaiting receipt")
    movement_snapshot(store, transfer, transfer["to_facility_id"], 1, user["id"])
    transfer["status"] = "received"
    store.put("transfer", transfer)
    if case["status"] == "dispatched":
        transition(store, case, "received", user["id"], now(), "Transfer received")
    return transfer
