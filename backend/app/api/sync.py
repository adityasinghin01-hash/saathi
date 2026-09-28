import hashlib
import json
import re
from threading import RLock

from fastapi import APIRouter, Request

from app.api import cases, stock, transfers
from app.api.shared import LABEL, USER_DEP, ApiError, store_for

router = APIRouter()
_op_lock = RLock()  # ASSUMPTION: one local process serves the SQLite demo.


def fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def execute_op(path: str, body: dict, request: Request, user: dict):
    if path.startswith("/") and not path.startswith("/api/v1/"):
        path = "/api/v1" + path
    if path == "/api/v1/cases":
        return cases.make_case(store_for(request), user, body)
    if path == "/api/v1/stock":
        return stock.record_stock(store_for(request), user, body)
    match = re.fullmatch(r"/api/v1/cases/([^/]+)/(verify|supply|confirm-received-by-patient|cancel)", path)
    if match:
        case_id, action = match.groups()
        if action == "verify":
            return cases.verify_case(case_id, body, request, user)
        if action == "supply":
            return cases.supply_case(case_id, body, request, user)
        if action == "cancel":
            return cases.cancel_case(case_id, body, request, user)
        return cases.confirm_received(case_id, request, user)
    match = re.fullmatch(r"/api/v1/transfers/([^/]+)/(approve|reject|dispatch|receive)", path)
    if match:
        transfer_id, action = match.groups()
        handlers = {"approve": transfers.approve_transfer, "reject": transfers.reject_transfer,
                    "dispatch": transfers.dispatch_transfer, "receive": transfers.receive_transfer}
        return handlers[action](transfer_id, request, user)
    if path == "/api/v1/transfers/draft":
        return transfers.draft_transfer(body, request, user)
    raise ApiError(422, "unsupported_op", "Offline path is not supported")


@router.post("/sync/batch")
def sync_batch(body: dict, request: Request, user: dict = USER_DEP):
    ops = body.get("ops")
    if not isinstance(ops, list):
        raise ApiError(422, "validation_error", "ops must be a list")
    store = store_for(request)
    results = []
    for op in ops:
        if not isinstance(op, dict) or not isinstance(op.get("op_id"), str) or not op["op_id"]:
            results.append({"op_id": op.get("op_id") if isinstance(op, dict) else None,
                            "status": "error", "error": {"code": "validation_error",
                                                         "message": "op_id is required"}})
            continue
        op_id = op["op_id"]
        key = f"{user['id']}:{op_id}"
        digest = fingerprint({"method": op.get("method"), "path": op.get("path"),
                              "body": op.get("body")})
        with _op_lock:
            prior = store.get("sync_op", key)
            if prior:
                if prior["digest"] != digest:
                    results.append({"op_id": op_id, "status": "error",
                                    "error": {"code": "idempotency_conflict",
                                              "message": "op_id reused with different content"}})
                else:
                    results.append({"op_id": op_id, "status": "duplicate", "result": prior["result"]})
                continue
            try:
                path = op.get("path")
                payload = op.get("body")
                if op.get("method") != "POST" or not isinstance(path, str) or not isinstance(payload, dict):
                    raise ApiError(422, "validation_error", "method POST, path and body are required")
                result = execute_op(path, payload, request, user)
            except ApiError as exc:
                results.append({"op_id": op_id, "status": "error",
                                "error": {"code": exc.code, "message": exc.message}})
                continue
            store.put("sync_op", {"id": key, "digest": digest, "result": result,
                                  "synthetic_label": LABEL})
            results.append({"op_id": op_id, "status": "applied", "result": result})
    return {"results": results, "synthetic_label": LABEL}
