"""Draft-only AI boundary for synthetic refill requests and stock transfers."""

import json
import logging
import os
import re
import time
from datetime import UTC, datetime, timedelta
from typing import Protocol

import google.auth
import httpx
from google import genai
from google.genai import errors, types

LABEL = "Synthetic demo data"
DEFAULT_MODELS = ("gemini-3.8-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash")
REQUEST_TIMEOUT_MS = 20_000
CALL_BUDGET_SECONDS = 40
logger = logging.getLogger(__name__)


class AIUnavailable(Exception):
    """The configured model could not complete a request."""


class UnsafeAIOutput(Exception):
    """Model output failed the contract or contained medical advice."""


class DraftAI(Protocol):
    def extract_voice(self, audio: bytes, language: str, mime_type: str,
                      patient: dict, drug_ids: list[str]) -> dict: ...

    def transfer_rationale(self, case: dict, donor: dict, distance_km: float) -> dict: ...


def contains_medical_advice(text: str) -> bool:
    """Flag medication instructions and blood-sugar numbers in patient-facing text."""
    english = re.search(
        r"\b(?:take|stop|start|increase|decrease|double|skip|change)\b"
        r".{0,60}\b(?:tablets?|pills?|doses?|medicines|medicine|medications?|drugs?|mg)\b",
        text,
        re.IGNORECASE,
    )
    instruction = (r"(?<![\u0900-\u0963\u0970-\u097f])"
                   r"(?:लो|लें|ले|बढ़ाओ|बढ़ाएं|बढ़ा|घटाओ|घटाएं|घटा|बंद|शुरू)"
                   r"(?![\u0900-\u0963\u0970-\u097f])")
    hindi = re.search(r"(?:दवा|गोली|खुराक).{0,30}" + instruction + "|" + instruction
                      + r".{0,30}(?:दवा|गोली|खुराक)", text)
    sugar_number = re.search(
        r"(?:blood sugar|glucose|ब्लड शुगर|शुगर|ग्लूकोज़).{0,25}\d"
        r"|\d.{0,25}(?:blood sugar|glucose|ब्लड शुगर|शुगर|ग्लूकोज़)",
        text,
        re.IGNORECASE,
    )
    return bool(english or hindi or sugar_number)


class DeterministicFakeAI:
    """Safe empty voice drafts and fixed transfer responses for local demos."""

    def extract_voice(self, audio: bytes, language: str, mime_type: str,
                      patient: dict, drug_ids: list[str]) -> dict:
        return {
            "fields": {"patient_id": patient["id"], "drug_id": None,
                       "requested_qty": None, "household_supply_days": None,
                       "attempted_at": None},
            "missing": ["drug_id", "requested_qty", "household_supply_days", "attempted_at"],
            "not_a_refill_report": None,
            "transcript": "", "synthetic_label": LABEL, "ai_source": "fake",
        }

    def transfer_rationale(self, case: dict, donor: dict, distance_km: float) -> dict:
        return {"rationale": (f"Synthetic demo draft: {donor['name']} has eligible stock for "
                              f"{case['requested_qty']} units; route distance {distance_km:.1f} km. "
                              "Officer approval required."), "ai_source": "fake"}


def _voice_schema(drug_ids: list[str]) -> dict:
    return {
        "type": "object", "additionalProperties": False,
        "properties": {
            "transcript": {"type": "string"},
            "not_a_refill_report": {"type": "boolean"},
            "fields": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "drug_id": {"anyOf": [{"type": "string", "enum": drug_ids},
                                          {"type": "null"}]},
                    "requested_qty": {"anyOf": [{"type": "integer", "minimum": 1},
                                                {"type": "null"}]},
                    "household_supply_days": {"anyOf": [{"type": "integer", "minimum": 0},
                                                        {"type": "null"}]},
                    "attempted_at": {"anyOf": [{"type": "string", "format": "date-time"},
                                              {"type": "null"}]},
                },
                "required": ["drug_id", "requested_qty", "household_supply_days", "attempted_at"],
            },
        },
        "required": ["transcript", "not_a_refill_report", "fields"],
    }


RATIONALE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"reason_code": {"type": "string",
                                   "enum": ["eligible_stock", "shortest_eligible_route"]}},
    "required": ["reason_code"],
}

TRANSCRIPT_SCHEMA = {"type": "object", "additionalProperties": False,
                     "properties": {"transcript": {"type": "string"}},
                     "required": ["transcript"]}


def _parse_voice(text: str | None, patient_id: str, drug_ids: list[str]) -> dict:
    try:
        result = json.loads(text or "")
        if not isinstance(result, dict) or set(result) != {
            "transcript", "not_a_refill_report", "fields"
        }:
            raise ValueError("Unexpected response fields")
        transcript = result["transcript"]
        not_a_refill_report = result["not_a_refill_report"]
        fields = result["fields"]
        if type(not_a_refill_report) is not bool:
            raise ValueError("Invalid report classification")
        if not isinstance(transcript, str) or not transcript.strip() or contains_medical_advice(transcript):
            raise ValueError("Unsafe transcript")
        if not isinstance(fields, dict) or set(fields) != {
            "drug_id", "requested_qty", "household_supply_days", "attempted_at"
        }:
            raise ValueError("Unexpected extracted fields")
        if fields["drug_id"] is not None and fields["drug_id"] not in drug_ids:
            raise ValueError("Unknown drug")
        if fields["requested_qty"] is not None and (
            type(fields["requested_qty"]) is not int or fields["requested_qty"] <= 0
        ):
            raise ValueError("Invalid requested quantity")
        if fields["household_supply_days"] is not None and (
            type(fields["household_supply_days"]) is not int or fields["household_supply_days"] < 0
        ):
            raise ValueError("Invalid household supply")
        attempted_at = fields["attempted_at"]
        if attempted_at is not None:
            if not isinstance(attempted_at, str):
                raise TypeError("Attempted time must be UTC")
            attempted_time = datetime.fromisoformat(attempted_at)
            if attempted_time.utcoffset() != timedelta(0):
                raise ValueError("Attempted time must be UTC")
            fields["attempted_at"] = attempted_time.isoformat().replace("+00:00", "Z")
        if not_a_refill_report and any(value is not None for value in fields.values()):
            raise ValueError("Non-refill report must not contain extracted fields")
    except (TypeError, ValueError, KeyError) as exc:
        raise UnsafeAIOutput("Voice extraction was rejected") from exc
    missing = [name for name in ("drug_id", "requested_qty", "household_supply_days",
                               "attempted_at") if fields[name] is None]
    return {"fields": {"patient_id": patient_id, **fields}, "missing": missing,
            "not_a_refill_report": not_a_refill_report, "transcript": transcript,
            "synthetic_label": LABEL}


class GeminiDraftAI:
    """Google Gen AI SDK adapter; the backend validates every generated result."""

    def __init__(self, client: genai.Client, models: list[str] | tuple[str, ...] | str):
        self.client = client
        self.models = [models] if isinstance(models, str) else list(models)
        if not self.models:
            raise ValueError("At least one Gemini model is required")

    def generate_structured(self, contents: list, schema: dict):
        """Return the SDK response and answering model within one 40-second call budget."""
        deadline = time.monotonic() + CALL_BUDGET_SECONDS
        for model in self.models:
            remaining_ms = int((deadline - time.monotonic()) * 1000)
            if remaining_ms <= 0:
                break
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0,
                        response_mime_type="application/json",
                        response_json_schema=schema,
                        http_options=types.HttpOptions(
                            timeout=min(REQUEST_TIMEOUT_MS, remaining_ms),
                            retry_options=types.HttpRetryOptions(attempts=1)),
                    ),
                )
                return response, model
            except Exception as exc:
                transient_api_error = isinstance(exc, errors.APIError) and exc.code in {429, 503}
                if not (transient_api_error or isinstance(exc, httpx.TimeoutException)):
                    raise AIUnavailable("Gemini request failed") from exc
                last_error = exc
        if "last_error" in locals():
            raise AIUnavailable("Gemini request failed") from last_error
        raise AIUnavailable("Gemini request failed")

    def extract_voice(self, audio: bytes, language: str, mime_type: str,
                      patient: dict, drug_ids: list[str]) -> dict:
        prompt = (
            f"Listen to this {language} audio. Transcribe the actual speech accurately. "
            "For Hindi speech, write the transcript in Devanagari; English words may stay in Latin. "
            "Classify whether the speaker reports an attempted medicine refill. General complaints "
            "about illness, doctors, or care without a refill attempt are not refill reports. "
            "If it is not a refill report, set not_a_refill_report=true and every field to null. "
            "Extract only facts explicitly said in the audio. Never infer a medicine from the "
            "patient's prescriptions, a typical dose or quantity, or the current date/time. "
            "Set each unspoken or unclear field to null, including household_supply_days; "
            "zero means the speaker explicitly said none remain. "
            f"Allowed drug IDs for mapping a spoken medicine name: {', '.join(drug_ids)}. "
            f"Current UTC date for resolving explicitly spoken relative dates: "
            f"{datetime.now(UTC).date().isoformat()}. "
            "When only a date is spoken, encode that date at 00:00:00Z; if no attempt date "
            "is spoken, attempted_at must be null. "
            "Do not give medical advice, dosing instructions, or blood-sugar values. "
            "Return only the requested JSON."
        )
        response, model = self.generate_structured(
            [prompt, types.Part.from_bytes(data=audio, mime_type=mime_type)],
            _voice_schema(drug_ids))
        result = _parse_voice(response.text, patient["id"], drug_ids)
        if language == "hi" and not re.search(r"[\u0900-\u097f]", result["transcript"]):
            script_prompt = (
                "इस रोमन लिपि में लिखी हिंदी बातचीत को देवनागरी में लिप्यंतरित करें। "
                "हर बोला गया शब्द, क्रम, और संख्या ज्यों की त्यों रखें। "
                "अंग्रेज़ी शब्द अंग्रेज़ी में रह सकते हैं। केवल JSON लौटाएं। पाठ: "
                + result["transcript"]
            )
            script_response, _ = self.generate_structured([script_prompt], TRANSCRIPT_SCHEMA)
            try:
                script_data = json.loads(script_response.text or "")
                if not isinstance(script_data, dict) or set(script_data) != {"transcript"}:
                    raise ValueError("Unexpected transcript response")
                script = script_data["transcript"]
                if not isinstance(script, str) or not script.strip() or contains_medical_advice(script):
                    raise ValueError("Unsafe transcript")
                result["transcript"] = script
            except (TypeError, ValueError) as exc:
                raise UnsafeAIOutput("Devanagari transcript was rejected") from exc
        return {**result, "ai_source": "gemini", "ai_model": model}

    def transfer_rationale(self, case: dict, donor: dict, distance_km: float) -> dict:
        prompt = (
            "Select the fact that best explains this proposed transfer. Do not add new facts "
            "or medical advice. Backend-checked facts: "
            f"donor={donor['name']}; eligible stock covers {case['requested_qty']} units; "
            f"route distance={distance_km:.1f} km; this is the nearest eligible donor; "
            "donor safety stock, expiry, and units checks pass."
        )
        response, model = self.generate_structured([prompt], RATIONALE_SCHEMA)
        try:
            result = json.loads(response.text or "")
            if not isinstance(result, dict) or set(result) != {"reason_code"}:
                raise ValueError("Unexpected rationale fields")
            if result["reason_code"] not in {"eligible_stock", "shortest_eligible_route"}:
                raise ValueError("Unknown rationale code")
        except (TypeError, ValueError) as exc:
            raise UnsafeAIOutput("Transfer rationale was rejected") from exc
        if result["reason_code"] == "shortest_eligible_route":
            rationale = (f"Synthetic demo draft: {donor['name']} is the nearest eligible donor for "
                         f"{case['requested_qty']} units at {distance_km:.1f} km. "
                         "Officer approval required.")
        else:
            rationale = DeterministicFakeAI().transfer_rationale(case, donor, distance_km)["rationale"]
        return {"rationale": rationale, "ai_source": "gemini", "ai_model": model}


def select_draft_ai(environ: dict | None = None) -> DraftAI:
    """Use API key by default; consult Vertex ADC only with explicit opt-in."""
    config = os.environ if environ is None else environ
    models = [name.strip() for name in config.get("GEMINI_MODELS", ",".join(DEFAULT_MODELS)).split(",")
              if name.strip()]
    if config.get("GEMINI_USE_VERTEX") == "1":
        try:
            credentials, adc_project = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"])
            project = config.get("GOOGLE_CLOUD_PROJECT") or adc_project
            if credentials is not None and project:
                client = genai.Client(vertexai=True, credentials=credentials, project=project,
                                      location=config.get("GOOGLE_CLOUD_LOCATION") or "global",
                                      http_options=types.HttpOptions(
                                          retry_options=types.HttpRetryOptions(attempts=1)))
                return GeminiDraftAI(client, models)
        except Exception as exc:  # noqa: BLE001 - preserve deterministic demo fallback
            logger.warning("Vertex ADC unavailable: %s", type(exc).__name__)
        return DeterministicFakeAI()
    key = config.get("GEMINI_API_KEY")
    if key:
        try:
            return GeminiDraftAI(genai.Client(
                api_key=key, http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(attempts=1))), models)
        except Exception as exc:  # noqa: BLE001 - preserve deterministic demo fallback
            logger.warning("Gemini API key client unavailable: %s", type(exc).__name__)
    return DeterministicFakeAI()
