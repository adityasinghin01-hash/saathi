import asyncio
import hashlib
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.routes import router
from app.api.shared import ApiError
from app.domain.ai import DraftAI, select_draft_ai
from app.seed.data import seed_if_empty
from app.storage.sqlite import SQLiteStore

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def create_app(db_url: str | None = None, ai: DraftAI | None = None) -> FastAPI:
    app = FastAPI(title="Refill Loop Synthetic Demo")
    default_db = f"sqlite:///{Path(__file__).resolve().parent.parent / 'refill_loop.db'}"
    app.state.store = SQLiteStore(db_url or os.getenv("DATABASE_URL", default_db))
    app.state.ai = ai if ai is not None else select_draft_ai()
    app.state.idempotency_lock = asyncio.Lock()  # ASSUMPTION: local demo runs one process.
    origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
               if origin.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
                       allow_headers=["X-Demo-User", "Idempotency-Key", "Content-Type"])
    seed_if_empty(app.state.store)
    app.state.store.prime_overview_forecasts()
    app.include_router(router, prefix="/api/v1")

    @app.middleware("http")
    async def idempotency(request: Request, call_next):
        key = request.headers.get("Idempotency-Key")
        if request.method != "POST" or not key:
            return await call_next(request)
        body = await request.body()
        actor = request.headers.get("X-Demo-User", "anonymous")
        record_id = hashlib.sha256(f"{actor}:{request.url.path}:{key}".encode()).hexdigest()
        digest = hashlib.sha256(body).hexdigest()
        async with app.state.idempotency_lock:
            prior = app.state.store.get("idempotency", record_id)
            if prior:
                if prior["digest"] != digest:
                    return JSONResponse(status_code=409, content={"error": {
                        "code": "idempotency_conflict", "message": "Key reused with different content"}})
                return JSONResponse(status_code=prior["status"], content=prior["response"])
            response = await call_next(request)
            content = b"".join([part async for part in response.body_iterator])
            if response.status_code < 500:
                try:
                    decoded = json.loads(content)
                except (ValueError, UnicodeDecodeError):
                    decoded = None
                if decoded is not None:
                    app.state.store.put("idempotency", {"id": record_id, "digest": digest,
                                                         "status": response.status_code,
                                                         "response": decoded})
            return Response(content=content, status_code=response.status_code,
                            headers=dict(response.headers), media_type=response.media_type)

    @app.exception_handler(ApiError)
    async def api_error_handler(request, exc: ApiError):
        return JSONResponse(status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "Invalid request"}})

    return app


app = create_app()
