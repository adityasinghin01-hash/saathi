"""Serve the latest saved offline evaluation results to district users."""

import json
import os
from pathlib import Path

from fastapi import APIRouter

from app.api.shared import LABEL, USER_DEP, require_role

router = APIRouter()
DEFAULT_RESULTS = Path(__file__).resolve().parents[2] / "eval" / "results"


@router.get("/evaluation/summary")
def evaluation_summary(user: dict = USER_DEP):
    require_role(user, "district_officer")
    directory = Path(os.getenv("EVALUATION_RESULTS_DIR", str(DEFAULT_RESULTS)))
    result = {"synthetic_label": LABEL}
    for name in ("forecast", "extraction"):
        path = directory / f"{name}.json"
        result[name] = json.loads(path.read_text()) if path.is_file() else None
    return result
