import shutil
import subprocess

import pytest

from eval.audio_eval import REAL, SYNTHETIC, _audio_bytes, _summarize, score_synthetic


def test_audio_score_reports_each_wrong_field_and_transcript_mismatch():
    sample = {
        "script": "कल मेटफॉर्मिन की तीस गोलियां मांगीं। दवा नहीं मिली। दो दिन की बची है।",
        "expected_refill_received": False,
        "expected_fields": {"patient_id": "patient-003", "drug_id": "metformin",
                            "requested_qty": 30, "household_supply_days": 2,
                            "attempted_date": "2026-09-28"},
    }
    prediction = {
        "transcript": sample["script"],
        "fields": {"patient_id": "patient-003", "drug_id": "metformin",
                   "requested_qty": 20, "household_supply_days": 2,
                   "attempted_at": "2026-09-27T09:00:00Z"},
    }
    scored = score_synthetic(sample, prediction)
    assert scored["field_correct"] == {
        "patient_id": True, "drug_id": True, "requested_qty": False,
        "household_supply_days": True, "attempted_date": False,
    }
    assert scored["wrong_fields"] == {
        "requested_qty": {"expected": 30, "actual": 20},
        "attempted_date": {"expected": "2026-09-28", "actual": "2026-09-27"},
    }
    assert scored["transcript_sane"] is True
    assert scored["refill_received_correct"] is True


def test_audio_score_marks_fallback_transcript_and_unavailable_fields():
    sample = {
        "script": "सोमवार को दवा मिल गई थी।",
        "expected_refill_received": True,
        "expected_fields": {"patient_id": "patient-003", "drug_id": "metformin",
                            "requested_qty": 20, "household_supply_days": 4,
                            "attempted_date": "2026-09-28"},
    }
    scored = score_synthetic(sample, {"transcript": "Synthetic demo transcription of a refill request.",
                                      "fields": {}})
    assert scored["transcript_sane"] is False
    assert scored["refill_received_correct"] is False
    assert len(scored["wrong_fields"]) == 5


def test_audio_score_accepts_romanized_hindi_with_spoken_fact_anchors():
    sample = {
        "script": "परसों सत्ताईस सितंबर को ग्लिमेपिराइड की बीस गोलियां मांगीं, दवा नहीं मिली।",
        "expected_refill_received": False,
        "expected_fields": {"patient_id": "patient-003", "drug_id": "glimepiride",
                            "requested_qty": 20, "household_supply_days": 0,
                            "attempted_date": "2026-09-27"},
    }
    prediction = {"transcript": "parso 27 sitambar ko glimepiride ki 20 goliyan mangin. dava nahi mili.",
                  "fields": {"patient_id": "patient-003", "drug_id": "glimepiride",
                             "requested_qty": 20, "household_supply_days": 0,
                             "attempted_at": "2026-09-27T09:00:00Z"}}
    scored = score_synthetic(sample, prediction)
    assert scored["transcript_sane"] is True
    assert scored["refill_received_correct"] is True
    assert scored["transcript_similarity"] < 0.6


def test_audio_summary_separates_gemini_accuracy_from_incidental_fallback_matches():
    rows = [
        {"ai_source": "gemini", "ai_model": "model", "http_status": 200, "latency_ms": 100,
         "field_correct": {"patient_id": True, "drug_id": True, "requested_qty": True,
                           "household_supply_days": True, "attempted_date": True},
         "transcript_sane": True, "refill_received_correct": True},
        {"ai_source": "fallback", "ai_model": None, "http_status": 200, "latency_ms": 200,
         "field_correct": {"patient_id": True, "drug_id": False, "requested_qty": False,
                           "household_supply_days": False, "attempted_date": False},
         "transcript_sane": False, "refill_received_correct": False},
    ]
    summary = _summarize(rows)
    assert summary["field_accuracy_live_gemini"]["drug_id"] == {
        "correct": 1, "total": 1, "rate": 1.0}
    assert summary["field_accuracy_all_clips"]["drug_id"] == {
        "correct": 1, "total": 2, "rate": 0.5}
    assert summary["transcript_sane_live_gemini"] == 1


def test_real_whatsapp_opus_is_sent_as_ogg_without_conversion():
    audio, mime = _audio_bytes(REAL / "r01.opus")
    assert mime == "audio/ogg"
    assert audio.startswith(b"OggS")


@pytest.mark.skipif(shutil.which("afconvert") is None, reason="macOS audio converter unavailable")
def test_real_m4a_is_converted_to_wav_for_voice_route(tmp_path):
    source = SYNTHETIC / "s01.wav"
    output = tmp_path / "short.m4a"
    subprocess.run(["afconvert", str(source), "-o", str(output), "-f", "m4af",
                    "-d", "LEI16"], check=True, capture_output=True)
    audio, mime = _audio_bytes(output)
    assert mime == "audio/wav"
    assert audio[:4] == b"RIFF"
    assert len(audio) > 10_000
