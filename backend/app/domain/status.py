from uuid import uuid4

PATH = {
    "reported": {"verified"},
    "verified": {"transfer_drafted"},
    "transfer_drafted": {"transfer_approved", "verified"},
    "transfer_approved": {"dispatched"},
    "dispatched": {"received"},
    "received": {"partially_supplied", "supplied"},
    "partially_supplied": {"partially_supplied", "supplied"},
    "supplied": {"closed"},
}


def can_transition(current: str, target: str, verification: str | None) -> bool:
    if target == "cancelled":
        return current not in {"closed", "cancelled"}
    if current == "verified" and target == "partially_supplied":
        return verification == "stock_available"
    if current == "verified" and target == "supplied":
        return verification == "stock_available"
    if current == "verified" and target == "closed":
        return verification == "household_only"
    if current == "verified" and target == "transfer_drafted":
        return verification == "confirmed_stockout"
    if current == "transfer_drafted" and target == "verified":
        return verification == "confirmed_stockout"
    return target in PATH.get(current, set())


def transition(store, case: dict, target: str, actor_id: str, at: str, note: str = "") -> dict:
    if not can_transition(case["status"], target, case["verification"]["result"]):
        from app.api.shared import ApiError
        raise ApiError(409, "illegal_transition", "Case transition is not allowed")
    event = {"id": f"event-{uuid4().hex}", "case_id": case["id"], "from_status": case["status"],
                 "to_status": target, "actor_id": actor_id, "at": at, "note": note,
                 "synthetic_label": "Synthetic demo data"}
    case = {**case, "status": target, "updated_at": at}
    store.put("case", case)
    store.put("case_event", event)
    return case
