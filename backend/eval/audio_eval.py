"""Score synthetic and optional real recordings through the live voice API route.

Run from backend/: PYTHONPATH=. .venv/bin/python -m eval.audio_eval
No case is confirmed or saved. The only provider calls are the route's normal Gemini calls.
"""

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import time
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from fastapi.testclient import TestClient

from app.domain.ai import GeminiDraftAI
from app.main import create_app

ROOT = Path(__file__).parent
SYNTHETIC = ROOT / "audio" / "synthetic"
REAL = ROOT / "audio" / "real"
RESULTS = ROOT / "results" / "audio.json"
FIELD_NAMES = ("patient_id", "drug_id", "requested_qty", "household_supply_days",
               "attempted_date")
MIME_TYPES = {".wav": "audio/wav", ".webm": "audio/webm", ".opus": "audio/ogg",
              ".ogg": "audio/ogg"}


def _normalized(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(re.findall(r"[\w\u0900-\u097f]+", text))


def _received(transcript: str) -> bool | None:
    text = _normalized(transcript)
    if re.search(r"मिल (?:गई|गयी|गया|चुकी|चुका) थी|मिली थी|\breceived\b|\bgot\b"
                 r"|\bmil(?:i)? (?:gai|gayi|gaya) thi\b", text):
        return True
    if re.search(r"नहीं|नही|\bnot\b|\bunavailable\b|\bout of stock\b"
                 r"|\bnahi(?:n)?\b", text):
        return False
    return None


def score_synthetic(sample: dict, prediction: dict | None) -> dict:
    prediction = prediction or {}
    fields = prediction.get("fields") or {}
    expected = sample["expected_fields"]
    actual = {name: fields.get(name) for name in FIELD_NAMES if name != "attempted_date"}
    actual["attempted_date"] = (fields.get("attempted_at") or "")[:10] or None
    correct = {name: actual[name] == expected[name] for name in FIELD_NAMES}
    wrong = {name: {"expected": expected[name], "actual": actual[name]}
             for name in FIELD_NAMES if not correct[name]}
    transcript = prediction.get("transcript") or ""
    similarity = SequenceMatcher(None, _normalized(sample["script"]),
                                 _normalized(transcript)).ratio()
    refill_received = _received(transcript)
    normalized_transcript = _normalized(transcript)
    romanized_anchors = (
        bool(re.search(r"\b[a-z]{3,}\b", normalized_transcript))
        and expected["drug_id"] in normalized_transcript
        and str(expected["requested_qty"]) in normalized_transcript
        and expected["attempted_date"][-2:].lstrip("0") in normalized_transcript
        and refill_received is not None
    )
    return {"field_correct": correct, "wrong_fields": wrong,
            "transcript_similarity": round(similarity, 3),
            "transcript_sane": similarity >= 0.6 or romanized_anchors,
            "refill_received_from_transcript": refill_received,
            "refill_received_correct": refill_received == sample["expected_refill_received"]}


def _audio_bytes(path: Path) -> tuple[bytes, str]:
    if path.suffix.lower() in MIME_TYPES:
        return path.read_bytes(), MIME_TYPES[path.suffix.lower()]
    if path.suffix.lower() == ".m4a":
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "converted.wav"
            if shutil.which("afconvert"):
                command = ["afconvert", str(path), "-o", str(output), "-f", "WAVE",
                           "-d", "LEI16@24000", "-c", "1"]
            else:
                command = ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path),
                           "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(output)]
            subprocess.run(command, check=True, capture_output=True)
            audio = output.read_bytes()
            if not audio.startswith(b"RIFF"):
                raise ValueError("M4A conversion did not produce WAV")
            return audio, "audio/wav"
    raise ValueError(f"Unsupported audio extension: {path.suffix}")


def _evaluate_one(client: TestClient, path: Path, metadata: dict | None,
                  default_user_id: str) -> dict:
    payload, mime_type = _audio_bytes(path)
    user_id = (metadata or {}).get("user_id", default_user_id)
    form = {"lang": (metadata or {}).get("lang", "hi")}
    if (metadata or {}).get("patient_id") and user_id.startswith("asha-"):
        form["patient_id"] = metadata["patient_id"]
    started = time.perf_counter()
    response = client.post("/api/v1/cases/voice", headers={"X-Demo-User": user_id},
                           data=form, files={"audio": (path.name, payload, mime_type)})
    latency = round((time.perf_counter() - started) * 1000, 1)
    body = response.json()
    row = {"id": path.stem, "file": path.name, "http_status": response.status_code,
           "latency_ms": latency, "ai_source": body.get("ai_source"),
           "ai_model": body.get("ai_model"), "transcript": body.get("transcript"),
           "transcript_devanagari": bool(re.search(r"[\u0900-\u097f]", body.get("transcript") or "")),
           "fields": body.get("fields"), "missing": body.get("missing"),
           "not_a_refill_report": body.get("not_a_refill_report"), "error": body.get("error")}
    if metadata and "expected_not_a_refill_report" in metadata:
        row["not_a_refill_report_correct"] = (
            body.get("not_a_refill_report") == metadata["expected_not_a_refill_report"])
    if metadata and "expected_fields" in metadata:
        if "script" in metadata and "expected_refill_received" in metadata:
            row.update(score_synthetic(metadata, body if response.status_code == 200 else None))
        else:
            expected = metadata["expected_fields"]
            actual = body.get("fields") or {}
            actual = {**actual, "attempted_date": (actual.get("attempted_at") or "")[:10] or None}
            row["wrong_fields"] = {
                name: {"expected": value, "actual": actual.get(name)}
                for name, value in expected.items() if actual.get(name) != value
            }
    return row


def _summarize(rows: list[dict]) -> dict:
    live_rows = [row for row in rows if row.get("ai_source") == "gemini"]
    counts = Counter(row.get("ai_model") for row in live_rows)

    def field_accuracy(group: list[dict]) -> dict:
        return {name: {"correct": sum(row.get("field_correct", {}).get(name, False)
                                      for row in group),
                       "total": len(group),
                       "rate": round(sum(row.get("field_correct", {}).get(name, False)
                                         for row in group) / len(group), 3) if group else None}
                for name in FIELD_NAMES}

    return {"clips": len(rows), "live_gemini_ok": sum(row["ai_source"] == "gemini"
                                                     for row in rows),
            "fallback": sum(row["ai_source"] == "fallback" for row in rows),
            "failed_http": sum(row["http_status"] != 200 for row in rows),
            "models_answered": dict(counts),
            "mean_latency_ms": round(sum(row["latency_ms"] for row in rows) / len(rows), 1)
            if rows else None,
            "field_accuracy_all_clips": field_accuracy(rows),
            "field_accuracy_live_gemini": field_accuracy(live_rows),
            "transcript_sane": sum(row.get("transcript_sane", False) for row in rows),
            "transcript_sane_live_gemini": sum(row.get("transcript_sane", False)
                                               for row in live_rows),
            "refill_outcome_correct": sum(row.get("refill_received_correct", False) for row in rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real-user-id", default="patient-user-003",
                        help="Demo user for unlabeled real clips; 003 has metformin/glimepiride, "
                             "006 has amlodipine/telmisartan")
    parser.add_argument("--pause-seconds", type=float, default=0,
                        help="Pause between live API calls to reduce provider rate limits")
    args = parser.parse_args()
    app = create_app("sqlite:///:memory:")
    if not isinstance(app.state.ai, GeminiDraftAI):
        raise TypeError("Live Gemini credential is required; no fake evaluation")
    synthetic_files = sorted(SYNTHETIC.glob("*.wav"))
    if len(synthetic_files) != 12:
        raise RuntimeError(f"Expected 12 synthetic WAV clips; found {len(synthetic_files)}")
    real_files = sorted(path for path in REAL.iterdir() if path.suffix.lower()
                        in {".m4a", ".webm", ".wav", ".opus", ".ogg"})
    with TestClient(app) as client:
        synthetic_rows = []
        for path in synthetic_files:
            if synthetic_rows:
                time.sleep(args.pause_seconds)
            metadata = json.loads(path.with_suffix(".json").read_text())
            row = _evaluate_one(client, path, metadata, metadata["user_id"])
            synthetic_rows.append(row)
            print(f"{path.stem}: HTTP {row['http_status']}, {row['ai_source']} "
                  f"{row['ai_model'] or '-'}, {row['latency_ms']} ms, "
                  f"wrong={list(row.get('wrong_fields', {}))}", flush=True)
        real_rows = []
        for path in real_files:
            if synthetic_rows or real_rows:
                time.sleep(args.pause_seconds)
            metadata_path = path.with_suffix(".json")
            metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else None
            row = _evaluate_one(client, path, metadata, args.real_user_id)
            real_rows.append(row)
            print(f"real {path.stem}: HTTP {row['http_status']}, {row['ai_source']} "
                  f"{row['ai_model'] or '-'}, {row['latency_ms']} ms; "
                  f"transcript={row['transcript']!r}; fields={row['fields']!r}", flush=True)
    result = {"label": "Synthetic demo data for synthetic clips only",
              "route": "POST /api/v1/cases/voice via FastAPI TestClient and live Gemini",
              "limitations": ["Gemini TTS is cleaner than real patient speech",
                              "Character similarity >=0.6 is only a transcript sanity proxy",
                              "Attempted date scores the UTC date, not exact time",
                              "Product schema has no refill outcome or facility field"],
              "synthetic": {"summary": _summarize(synthetic_rows), "clips": synthetic_rows},
              "real": {"count": len(real_rows), "clips": real_rows}}
    RESULTS.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {RESULTS}", flush=True)


if __name__ == "__main__":
    main()
