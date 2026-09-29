from fastapi import APIRouter

from app.api import cases, demo, evaluation, notifications, reference, stock, sync, transfers, voice
from app.api.shared import LABEL

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "label": LABEL}


router.include_router(reference.router)
router.include_router(demo.router)
router.include_router(evaluation.router)
router.include_router(cases.router)
router.include_router(notifications.router)
router.include_router(stock.router)
router.include_router(transfers.router)
router.include_router(voice.router)
router.include_router(sync.router)
