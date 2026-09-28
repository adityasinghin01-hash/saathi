from datetime import UTC, datetime

from fastapi import Depends, Header, Request

LABEL = "Synthetic demo data"


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message


def store_for(request: Request):
    return request.app.state.store


def user_for(request: Request, x_demo_user: str | None = Header(default=None)) -> dict:
    if not x_demo_user:
        raise ApiError(401, "unauthorized", "Select a demo user")
    user = store_for(request).get("user", x_demo_user)
    if not user:
        raise ApiError(401, "unauthorized", "Unknown demo user")
    return user


USER_DEP = Depends(user_for)


def require_role(user: dict, *roles: str) -> None:
    if user["role"] not in roles:
        raise ApiError(403, "forbidden", "Role cannot use this endpoint")


def get_or_404(store, kind: str, id: str) -> dict:
    item = store.get(kind, id)
    if not item:
        raise ApiError(404, "not_found", f"{kind} not found")
    return item
