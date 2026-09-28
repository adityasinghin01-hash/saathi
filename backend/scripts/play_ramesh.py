"""Play the complete synthetic Ramesh story against a running API server."""

import argparse
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def call(base_url: str, method: str, path: str, user: str, body: dict | None = None) -> dict:
    payload = json.dumps(body).encode() if body is not None else None
    request = Request(base_url.rstrip("/") + "/api/v1" + path, data=payload, method=method,
                      headers={"X-Demo-User": user, "Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"{method} {path}: HTTP {exc.code} {detail}") from exc


def play(base_url: str) -> None:
    officer = "officer-1"
    reset = call(base_url, "POST", "/demo/reset", officer)
    print("Reset:", reset)
    ids = call(base_url, "GET", "/demo/scenario/ramesh", officer)
    print("Scenario:", ids)
    patient_user = "patient-user-001"
    pharmacist = ids["pharmacist_id"]
    case = call(base_url, "POST", "/cases", patient_user, {
        "patient_id": ids["patient_id"], "drug_id": ids["drug_id"],
        "requested_qty": 30, "household_supply_days": 0,
        "attempted_at": "2026-09-28T09:00:00Z", "channel": "manual"})
    print("Report:", case["id"], case["status"])
    case_id = case["id"]
    verified = call(base_url, "POST", f"/cases/{case_id}/verify", pharmacist,
                    {"result": "confirmed_stockout", "on_hand": 0})
    print("Verify:", verified["status"])
    transfer = call(base_url, "POST", "/transfers/draft", officer, {"case_id": case_id})
    assert transfer["from_facility_id"] == ids["donor_facility_id"]
    print("Draft:", transfer["id"], transfer["from_facility_id"])
    transfer_id = transfer["id"]
    for action, actor in (("approve", officer), ("dispatch", officer), ("receive", pharmacist)):
        transfer = call(base_url, "POST", f"/transfers/{transfer_id}/{action}", actor)
        print(action.title() + ":", transfer["status"])
    supplied = call(base_url, "POST", f"/cases/{case_id}/supply", pharmacist,
                    {"quantity": 30})
    print("Supply:", supplied["status"])
    closed = call(base_url, "POST", f"/cases/{case_id}/confirm-received-by-patient",
                  patient_user)
    print("Close:", closed["status"])
    detail = call(base_url, "GET", f"/cases/{case_id}", officer)
    print("Events:", " -> ".join(event["to_status"] for event in detail["events"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    play(parser.parse_args().base_url)
