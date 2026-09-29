"""Resettable deterministic demo and its named story identifiers."""

import os

from fastapi import APIRouter, Request

from app.api.shared import USER_DEP, ApiError, now, store_for
from app.seed.data import seed_if_empty

router = APIRouter()


@router.post("/demo/reset")
def demo_reset(request: Request, user: dict = USER_DEP):
    if os.getenv("DEMO_MODE") != "1":
        raise ApiError(403, "demo_disabled", "Demo reset is disabled")
    store = store_for(request)
    store.reset()
    seed_if_empty(store)
    store.prime_overview_forecasts()
    return {"ok": True, "seeded_at": now()}


@router.get("/demo/scenario/ramesh")
def ramesh_scenario(request: Request, user: dict = USER_DEP):
    store = store_for(request)
    patient = store.get("patient", "patient-001")
    if patient is None:
        raise ApiError(404, "not_found", "Ramesh scenario is unavailable")
    return {"patient_id": patient["id"], "asha_id": patient["asha_id"],
            "pharmacist_id": "pharmacist-1", "district_officer_id": "officer-1",
            "facility_id": patient["facility_id"], "donor_facility_id": "phc-2",
            "drug_id": "metformin"}
