from fastapi import APIRouter, Request

from app.api.shared import USER_DEP, ApiError, get_or_404, require_role, store_for

router = APIRouter()


@router.get("/demo/users")
def demo_users(request: Request):
    # ASSUMPTION: picker is public so the first demo user can be selected.
    return store_for(request).list("user")


@router.get("/me")
def me(user: dict = USER_DEP):
    return user


@router.get("/facilities")
def facilities(request: Request, user: dict = USER_DEP):
    return store_for(request).list("facility")


@router.get("/drugs")
def drugs(request: Request, user: dict = USER_DEP):
    return store_for(request).list("drug")


@router.get("/patients")
def patients(request: Request, user: dict = USER_DEP):
    require_role(user, "patient", "asha", "pharmacist", "district_officer")
    store = store_for(request)
    home = get_or_404(store, "facility", user["facility_id"])
    prescriptions = store.list("prescription")
    cases = store.list("case")
    rows = []
    for patient in store.list("patient"):
        if user["role"] == "patient" and patient["id"] != user.get("patient_id"):
            continue
        if user["role"] == "asha" and patient["asha_id"] != user["id"]:
            continue
        if user["role"] == "pharmacist" and patient["facility_id"] != user["facility_id"]:
            continue
        if user["role"] == "district_officer":
            facility = get_or_404(store, "facility", patient["facility_id"])
            if facility["district"] != home["district"]:
                continue
        open_cases = [case for case in cases if case["patient_id"] == patient["id"]
                      and case["status"] not in {"closed", "cancelled"}]
        latest_case = max(open_cases, key=lambda case: (case["updated_at"], case["id"]),
                          default=None)
        rows.append({**patient,
                     "prescriptions": [rx for rx in prescriptions if rx["patient_id"] == patient["id"]],
                     "open_case": latest_case})
    return sorted(rows, key=lambda patient: patient["id"])


@router.get("/patients/{patient_id}")
def patient_detail(patient_id: str, request: Request, user: dict = USER_DEP):
    require_role(user, "patient", "asha", "pharmacist")
    store = store_for(request)
    patient = get_or_404(store, "patient", patient_id)
    if user["role"] == "patient" and user.get("patient_id") != patient_id:
        raise ApiError(403, "forbidden", "Patient is outside your scope")
    if user["role"] == "asha" and patient["asha_id"] != user["id"]:
        raise ApiError(403, "forbidden", "Patient is outside your scope")
    if user["role"] == "pharmacist" and patient["facility_id"] != user["facility_id"]:
        raise ApiError(403, "forbidden", "Patient is outside your scope")
    prescriptions = [row for row in store.list("prescription") if row["patient_id"] == patient_id]
    return {**patient, "prescriptions": prescriptions}
