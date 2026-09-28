from fastapi import APIRouter, File, Form, Request, UploadFile

from app.api.cases import make_case
from app.api.shared import USER_DEP, ApiError, get_or_404, require_role, store_for
from app.domain.ai import (
    AIUnavailable,
    DeterministicFakeAI,
    UnsafeAIOutput,
    contains_medical_advice,
)

router = APIRouter()
AUDIO_FILE = File(...)
SUPPORTED_AUDIO = {"audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg", "audio/wav",
                   "audio/x-wav", "audio/wave"}


@router.post("/cases/voice")
async def voice_extract(request: Request, audio: UploadFile = AUDIO_FILE, lang: str = Form(...),
                        patient_id: str | None = Form(default=None),
                        user: dict = USER_DEP):
    require_role(user, "patient", "asha")
    if lang not in {"hi", "en"}:
        raise ApiError(422, "validation_error", "Unsupported language")
    media_type = (audio.content_type or "").partition(";")[0].strip().lower()
    if media_type not in SUPPORTED_AUDIO:
        raise ApiError(415, "unsupported_audio", "Use webm, ogg, mp4, mpeg, or wav audio")
    content = await audio.read()
    if not content:
        raise ApiError(422, "validation_error", "Audio is required")
    store = store_for(request)
    selected_id = user.get("patient_id") if user["role"] == "patient" else patient_id
    if not selected_id:
        # ASSUMPTION: an ASHA must identify the assigned patient in multipart form data.
        raise ApiError(422, "validation_error", "patient_id is required")
    patient = get_or_404(store, "patient", selected_id)
    if user["role"] == "asha" and patient["asha_id"] != user["id"]:
        raise ApiError(403, "forbidden", "Patient is outside your scope")
    prescriptions = sorted((rx for rx in store.list("prescription")
                            if rx["patient_id"] == selected_id and rx["active"]),
                           key=lambda row: row["id"])
    if not prescriptions:
        raise ApiError(422, "validation_error", "No active prescription")
    drug_ids = list(dict.fromkeys(rx["drug_id"] for rx in prescriptions))
    try:
        result = request.app.state.ai.extract_voice(content, lang, media_type, patient,
                                                    drug_ids)
    except AIUnavailable:
        result = DeterministicFakeAI().extract_voice(content, lang, media_type, patient,
                                                     drug_ids)
        result["ai_source"] = "fallback"
    except UnsafeAIOutput as exc:
        raise ApiError(422, "ai_output_rejected", "Voice extraction needs manual review") from exc
    return result


@router.post("/cases/voice/confirm")
def voice_confirm(body: dict, request: Request, user: dict = USER_DEP):
    require_role(user, "patient", "asha")
    fields = body.get("fields")
    transcript = body.get("transcript")
    if not isinstance(fields, dict) or not isinstance(transcript, str):
        raise ApiError(422, "validation_error", "Confirmed fields and transcript are required")
    if contains_medical_advice(transcript):
        raise ApiError(422, "medical_advice", "Medical advice text cannot be saved")
    return make_case(store_for(request), user, {**fields, "channel": "voice",
                                                 "transcript": transcript})
