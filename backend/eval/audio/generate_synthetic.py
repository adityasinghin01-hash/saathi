"""Generate labeled synthetic Hindi speech; never use these clips as real-patient evidence.

Run from backend/: PYTHONPATH=. .venv/bin/python -m eval.audio.generate_synthetic
Existing WAV/JSON pairs are left intact. API credentials are loaded from backend/.env.
"""

import base64
import io
import json
import os
import time
import wave
from pathlib import Path

import httpx
from dotenv import load_dotenv

DIRECTORY = Path(__file__).parent / "synthetic"
MODELS = ("gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts")
STYLE = "Natural conversational Hindi from a rural patient or ASHA worker; clear normal pace."
SAMPLES = [
    ("s01", "patient-003", "मेरी मेटफॉर्मिन की दवा खत्म हो गई। कल अट्ठाईस सितंबर को सुंदरपुर पी एच सी गया था। तीस गोलियां मांगी, दवा नहीं मिली। घर में दो दिन की बची है।", "metformin", 30, 2, "2026-09-28", False, False),
    ("s02", "patient-003", "परसों सत्ताईस सितंबर को सुंदरपुर पी एच सी में ग्लिमेपिराइड की बीस गोलियां मांगी थीं। दवा नहीं मिली। घर में एक भी दिन की दवा नहीं है।", "glimepiride", 20, 0, "2026-09-27", False, False),
    ("s03", "patient-006", "सोमवार अट्ठाईस सितंबर को उदयपुर पी एच सी गई थी। अम्लोडिपिन की पंद्रह गोलियां मांगीं, मिली नहीं। घर पर तीन दिन की दवा बची है।", "amlodipine", 15, 3, "2026-09-28", False, False),
    ("s04", "patient-006", "कल अट्ठाईस सितंबर को उदयपुर पी एच सी से टेल्मिसार्टन की दस गोलियां मांगी थीं। नहीं मिलीं। मेरे पास एक दिन की दवा है।", "telmisartan", 10, 1, "2026-09-28", False, False),
    ("s05", "patient-003", "परसों सत्ताईस सितंबर को मेटफॉर्मिन लेने सुंदरपुर पी एच सी गया। पच्चीस गोलियां चाहिए थीं, मगर नहीं मिलीं। घर में चार दिन की बची हैं।", "metformin", 25, 4, "2026-09-27", False, False),
    ("s06", "patient-003", "सोमवार अट्ठाईस सितंबर को ग्लिमेपिराइड लेने गया था। सुंदरपुर पी एच सी में तीस गोलियां मांगीं, नहीं मिलीं। घर पर बस एक दिन की हैं।", "glimepiride", 30, 1, "2026-09-28", False, False),
    ("s07", "patient-006", "कल अट्ठाईस सितंबर को उदयपुर पी एच सी में अम्लोडिपिन की बारह गोलियां मांगी थीं। दवा नहीं मिली और घर पर दवा खत्म है।", "amlodipine", 12, 0, "2026-09-28", False, False),
    ("s08", "patient-006", "परसों सत्ताईस सितंबर को टेल्मिसार्टन लेने उदयपुर पी एच सी गया था। चौबीस गोलियां मांगीं, दवा नहीं मिली। दो दिन की घर पर बची है।", "telmisartan", 24, 2, "2026-09-27", False, False),
    ("s09", "patient-003", "सोमवार अट्ठाईस सितंबर को सुंदरपुर पी एच सी से मेटफॉर्मिन की बीस गोलियां मांगी थीं। दवा मिल गई थी। अब घर में चार दिन की बची है।", "metformin", 20, 4, "2026-09-28", True, False),
    ("s10", "patient-006", "सोमवार अट्ठाईस सितंबर को उदयपुर पी एच सी में अम्लोडिपिन की अठारह गोलियां मांगी थीं। दवा मिल गई थी। घर में तीन दिन की बची है।", "amlodipine", 18, 3, "2026-09-28", True, False),
    ("s11", "patient-003", "कल अट्ठाईस सितंबर को सुंदरपुर पी एच सी गई थी। Glimepiride की sixteen tablets मांगीं, stock नहीं था। घर पर two days की दवा बची है।", "glimepiride", 16, 2, "2026-09-28", False, True),
    ("s12", "patient-006", "परसों सत्ताईस सितंबर को उदयपुर पी एच सी गया। Telmisartan की thirty tablets चाहिए थीं, medicine नहीं मिली। घर पर five days की बची है।", "telmisartan", 30, 5, "2026-09-27", False, True),
]


def generate_one(client: httpx.Client, script: str) -> tuple[bytes, str, float]:
    payload = {
        "contents": [{"role": "user", "parts": [{"text": script,
                     "speech_metadata": {"style": STYLE}}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": {"voice": "Kore"}}},
    }
    for model in MODELS:
        for attempt in range(3):
            started = time.monotonic()
            response = client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                json=payload,
            )
            seconds = time.monotonic() - started
            if response.status_code in {429, 503} and attempt < 2:
                time.sleep(2**attempt)
                continue
            if response.status_code != 200:
                print(f"TTS {model}: HTTP {response.status_code}", flush=True)
                break
            part = response.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
            audio = base64.b64decode(part["data"])
            if part.get("mimeType") != "audio/wav" or not audio.startswith(b"RIFF"):
                raise ValueError(f"Unexpected TTS format from {model}")
            return audio, model, seconds
    raise RuntimeError("Both TTS models failed")


def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is required")
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers={"x-goog-api-key": key}, timeout=90) as client:
        for sample in SAMPLES:
            clip_id, patient_id, script, drug_id, qty, days, date, received, hinglish = sample
            wav_path = DIRECTORY / f"{clip_id}.wav"
            json_path = DIRECTORY / f"{clip_id}.json"
            if wav_path.exists() and json_path.exists():
                print(f"{clip_id}: already present", flush=True)
                continue
            audio, model, latency = generate_one(client, script)
            with wave.open(io.BytesIO(audio)) as wav:
                duration = wav.getnframes() / wav.getframerate()
            if duration >= 20:
                raise ValueError(f"{clip_id} exceeds 20 seconds: {duration:.1f}")
            metadata = {
                "id": clip_id, "synthetic_label": "Synthetic demo data",
                "recording_kind": "Gemini TTS, not a real patient or ASHA recording",
                "tts_model": model, "tts_voice": "Kore", "tts_latency_seconds": round(latency, 3),
                "duration_seconds": round(duration, 3), "script": script,
                "patient_id": patient_id, "user_id": patient_id.replace("patient-", "patient-user-"),
                "expected_fields": {"patient_id": patient_id, "drug_id": drug_id,
                                    "requested_qty": qty, "household_supply_days": days,
                                    "attempted_date": date},
                "expected_refill_received": received, "hinglish": hinglish,
                "audio_mime_type": "audio/wav",
            }
            wav_path.write_bytes(audio)
            json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
            print(f"{clip_id}: {model}, {duration:.1f}s", flush=True)


if __name__ == "__main__":
    main()
