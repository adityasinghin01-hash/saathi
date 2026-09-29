"""Patient and ASHA notices derived from case audit events."""

from fastapi import APIRouter, Request

from app.api.cases import can_see_case
from app.api.shared import USER_DEP, ApiError, get_or_404, now, store_for

router = APIRouter()

KINDS = {"dispatched": "on_the_way", "received": "arrived",
         "supplied": "given", "partially_supplied": "given"}


def _can_see_notification(store, case: dict, user: dict) -> bool:
    return user["role"] in {"patient", "asha"} and can_see_case(store, case, user)


def _message(kind: str, drug: dict, facility: dict) -> tuple[str, str]:
    drug_hi, drug_en = drug["name_hi"], drug["name"]
    facility_hi, facility_en = facility["name_hi"], facility["name"]
    if kind == "on_the_way":
        return (f"आपकी {drug_hi} {facility_hi} के लिए भेज दी गई है।",
                f"Your {drug_en} is on the way to {facility_en}.")
    if kind == "arrived":
        return (f"आपकी {drug_hi} {facility_hi} पहुँच गई है। आज ले लें।",
                f"Your {drug_en} has reached {facility_en}. Collect it today.")
    return (f"आपको {facility_hi} में {drug_hi} दे दी गई है।",
            f"You were given {drug_en} at {facility_en}.")


@router.get("/notifications")
def list_notifications(request: Request, user: dict = USER_DEP):
    if user["role"] not in {"patient", "asha"}:
        return []
    store = store_for(request)
    cases = {case["id"]: case for case in store.list("case")
             if _can_see_notification(store, case, user)}
    reads = {row["event_id"] for row in store.list("notification_read")
             if row["user_id"] == user["id"]}
    rows = []
    for event in store.list("case_event"):
        kind = KINDS.get(event["to_status"])
        case = cases.get(event["case_id"])
        if kind is None or case is None:
            continue
        drug = get_or_404(store, "drug", case["drug_id"])
        facility = get_or_404(store, "facility", case["facility_id"])
        hi, en = _message(kind, drug, facility)
        rows.append({"id": event["id"], "case_id": case["id"], "kind": kind,
                     "drug_id": case["drug_id"], "facility_id": case["facility_id"],
                     "at": event["at"], "read": event["id"] in reads, "hi": hi, "en": en})
    return sorted(rows, key=lambda row: (row["at"], row["id"]), reverse=True)


@router.post("/notifications/{event_id}/read")
def mark_notification_read(event_id: str, request: Request, user: dict = USER_DEP):
    store = store_for(request)
    event = store.get("case_event", event_id)
    case = store.get("case", event["case_id"]) if event else None
    if (event is None or event["to_status"] not in KINDS or case is None
            or not _can_see_notification(store, case, user)):
        raise ApiError(404, "not_found", "Notification not found")
    store.put("notification_read", {"id": f"{user['id']}:{event_id}",
                                    "user_id": user["id"], "event_id": event_id,
                                    "read_at": now()})
    return {"id": event_id, "read": True}
