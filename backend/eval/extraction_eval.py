"""Score a hand-authored Hindi/Hinglish corpus against the product extraction schema.

This is transcript-only evaluation. Live mode sends text through the same JSON schema and
validator as voice extraction; it does not test speech recognition or audio quality.
"""

import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

from app.domain.ai import (
    AIUnavailable,
    DeterministicFakeAI,
    GeminiDraftAI,
    _parse_voice,
    _voice_schema,
    select_draft_ai,
)

LABEL = "Synthetic demo data"
CORPUS = json.loads((Path(__file__).parent / "hindi_corpus.json").read_text())
DRUG_STRENGTH = {"metformin": "500 mg", "glimepiride": "1 mg",
                 "amlodipine": "5 mg", "telmisartan": "40 mg"}
FIELDS = ("medicine", "strength", "facility", "date", "requested_qty",
          "received_qty", "household_supply_days", "negated")
NEGATION = re.compile(r"नहीं|नही|not available|unavailable", re.IGNORECASE)


def score_case(case: dict, prediction: dict | None) -> dict[str, bool]:
    gold = case["gold"]
    fields = prediction.get("fields", {}) if prediction else {}
    transcript = prediction.get("transcript", "") if prediction else ""
    drug_id = fields.get("drug_id")
    attempted_at = fields.get("attempted_at") or ""
    predicted = {
        "medicine": drug_id,
        "strength": DRUG_STRENGTH.get(drug_id),
        "facility": fields.get("facility"),
        "date": attempted_at[:10],
        "requested_qty": fields.get("requested_qty"),
        "received_qty": fields.get("received_qty"),
        "household_supply_days": fields.get("household_supply_days"),
        "negated": bool(NEGATION.search(transcript)),
    }
    return {field: predicted[field] == gold[field] for field in FIELDS}


def _summarize(predictions: list[dict | None], latencies: list[float],
               cost: float | None, mode: str, failures: list[str]) -> dict:
    scores = [score_case(case, prediction) for case, prediction in zip(CORPUS, predictions)]
    return {"mode": mode, "samples": len(CORPUS), "failed_calls": len(failures),
            "successful_calls": len(CORPUS) - len(failures),
            "failure_types": failures, "field_accuracy": {
                field: round(sum(score[field] for score in scores) / len(CORPUS), 3)
                for field in FIELDS},
            "negation_errors": sum(not score["negated"] for score in scores),
            "latency_ms_mean": round(sum(latencies) / len(latencies), 3),
            "estimated_cost_usd": cost}


def evaluate_fake() -> dict:
    fake = DeterministicFakeAI()
    predictions = []
    latencies = []
    for case in CORPUS:
        start = time.perf_counter()
        prediction = fake.extract_voice(case["transcript"].encode(), "hi", "text/plain",
                                        {"id": case["id"]}, list(DRUG_STRENGTH))
        latencies.append((time.perf_counter() - start) * 1000)
        predictions.append(prediction)
    return _summarize(predictions, latencies, 0.0, "deterministic_fake", [])


def evaluate_live(api_key: str) -> dict:
    config = {"GEMINI_API_KEY": api_key}
    if os.getenv("GEMINI_MODELS"):
        config["GEMINI_MODELS"] = os.environ["GEMINI_MODELS"]
    ai = select_draft_ai(config)
    if not isinstance(ai, GeminiDraftAI):
        raise TypeError("Gemini API key client could not be created")
    predictions = []
    latencies = []
    failures = []
    failure_codes = []
    models_answered = {}
    input_tokens = 0
    output_tokens = 0
    schema = _voice_schema(list(DRUG_STRENGTH))
    for case in CORPUS:
        prompt = ("Extract only stated refill facts from this synthetic Hindi/Hinglish transcript. "
                  "Preserve the exact transcript, including negations. Return the product JSON "
                  "schema. Use 2026 as the year. Do not give medical advice. Allowed drug IDs: "
                  f"{', '.join(DRUG_STRENGTH)}. Transcript: {case['transcript']}")
        start = time.perf_counter()
        try:
            response, model = ai.generate_structured([prompt], schema)
            prediction = _parse_voice(response.text, case["id"], list(DRUG_STRENGTH))
            models_answered[model] = models_answered.get(model, 0) + 1
            usage = response.usage_metadata
            if usage:
                input_tokens += usage.prompt_token_count or 0
                output_tokens += usage.candidates_token_count or 0
        except Exception as exc:  # noqa: BLE001 - preserve partial evaluation, never fake success
            prediction = None
            failures.append(type(exc).__name__)
            cause = exc.__cause__ if isinstance(exc, AIUnavailable) else exc
            failure_codes.append(getattr(cause, "code", None))
        latencies.append((time.perf_counter() - start) * 1000)
        predictions.append(prediction)
    input_rate = os.getenv("GEMINI_INPUT_USD_PER_MILLION")
    output_rate = os.getenv("GEMINI_OUTPUT_USD_PER_MILLION")
    cost = (round((input_tokens * float(input_rate) + output_tokens * float(output_rate))
                  / 1_000_000, 6) if input_rate and output_rate else None)
    result = _summarize(predictions, latencies, cost, "gemini_transcript_text", failures)
    result.update({"models_tried": ai.models, "models_answered": models_answered,
                   "failure_codes": failure_codes,
                   "input_tokens": input_tokens, "output_tokens": output_tokens,
                   "cost_note": "Set verified per-million-token rates in GEMINI_INPUT_USD_PER_MILLION "
                                "and GEMINI_OUTPUT_USD_PER_MILLION to estimate cost."})
    return result


def evaluate() -> dict:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    result = {"label": LABEL, "corpus": "30 hand-authored synthetic Hindi/Hinglish transcripts",
              "limitations": ["Transcript-only; audio recognition is not evaluated",
                              "Product schema has no facility, received quantity, or negation field",
                              "Strength is normalized from predicted drug ID"],
              "fake": evaluate_fake()}
    key = os.getenv("GEMINI_API_KEY")
    if key:
        attempts = []
        for attempt in range(3):
            live = evaluate_live(key)
            attempts.append({"successful_calls": live["successful_calls"],
                             "failed_calls": live["failed_calls"],
                             "models_answered": live["models_answered"],
                             "latency_ms_mean": live["latency_ms_mean"],
                             "failure_codes": live["failure_codes"]})
            if live["failed_calls"] != len(CORPUS) or set(live["failure_codes"]) != {503}:
                break
            if attempt < 2:
                time.sleep(300)
        live["attempts"] = attempts
        result["live"] = live
    else:
        result["live"] = {"status": "not_run_no_api_key"}
    return result


if __name__ == "__main__":
    path = Path(__file__).parent / "results" / "extraction.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evaluate(), ensure_ascii=False, indent=2) + "\n")
