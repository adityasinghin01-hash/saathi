import pytest

from tests.conftest import auth


def test_voice_fake_extracts_without_saving_until_confirmed(client):
    before = len(client.get("/api/v1/cases", headers=auth("patient-user-001")).json())
    response = client.post("/api/v1/cases/voice", headers=auth("patient-user-001"),
                           data={"lang": "hi"}, files={"audio": ("demo.wav", b"synthetic audio", "audio/wav")})
    assert response.status_code == 200
    extraction = response.json()
    assert extraction["synthetic_label"] == "Synthetic demo data"
    assert extraction["ai_source"] == "fake"
    assert extraction["not_a_refill_report"] is None
    assert extraction["fields"]["patient_id"] == "patient-001"
    assert extraction["missing"] == ["drug_id", "requested_qty", "household_supply_days",
                                     "attempted_at"]
    assert all(extraction["fields"][name] is None for name in extraction["missing"])
    assert len(client.get("/api/v1/cases", headers=auth("patient-user-001")).json()) == before
    confirmed = client.post("/api/v1/cases/voice/confirm", headers=auth("patient-user-001"),
                            json=extraction)
    assert confirmed.status_code == 422
    assert "drug_id" in confirmed.json()["error"]["message"]
    assert len(client.get("/api/v1/cases", headers=auth("patient-user-001")).json()) == before
    extraction["fields"].update({"drug_id": "metformin", "requested_qty": 30,
                                 "household_supply_days": 0,
                                 "attempted_at": "2026-09-28T09:00:00Z"})
    confirmed = client.post("/api/v1/cases/voice/confirm", headers=auth("patient-user-001"),
                            json=extraction)
    assert confirmed.status_code == 200
    assert confirmed.json()["channel"] == "voice"
    assert confirmed.json()["transcript"] == extraction["transcript"]


def test_voice_rejects_unsupported_audio(client):
    response = client.post("/api/v1/cases/voice", headers=auth("patient-user-001"),
                           data={"lang": "en"},
                           files={"audio": ("demo.txt", b"audio", "text/plain")})
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_audio"


def test_voice_provider_failure_uses_marked_fallback(client):
    from app.domain.ai import AIUnavailable

    class Unavailable:
        def extract_voice(self, *args):
            raise AIUnavailable("failed")

    previous = client.app.state.ai
    client.app.state.ai = Unavailable()
    try:
        response = client.post("/api/v1/cases/voice", headers=auth("patient-user-001"),
                               data={"lang": "en"},
                               files={"audio": ("demo.wav", b"audio", "audio/wav")})
    finally:
        client.app.state.ai = previous
    assert response.status_code == 200
    assert response.json()["ai_source"] == "fallback"
    assert response.json()["not_a_refill_report"] is None
    assert response.json()["missing"] == ["drug_id", "requested_qty", "household_supply_days",
                                            "attempted_at"]
    assert all(response.json()["fields"][name] is None
               for name in response.json()["missing"])


def test_voice_confirmation_rejects_medical_advice(client):
    response = client.post("/api/v1/cases/voice/confirm", headers=auth("patient-user-001"),
                           json={"fields": {"patient_id": "patient-001", "drug_id": "metformin",
                                            "requested_qty": 30, "household_supply_days": 0,
                                            "attempted_at": "2026-09-28T09:00:00Z"},
                                 "transcript": "Take two tablets daily to treat diabetes."})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "medical_advice"


@pytest.mark.parametrize("mime_type", [
    "audio/webm", "audio/webm;codecs=opus", "audio/ogg", "audio/ogg; codecs=opus",
    "audio/mp4", "audio/mp4; codecs=mp4a.40.2", "audio/mpeg", "audio/wav", "audio/x-wav",
])
def test_voice_accepts_supported_audio_formats(client, mime_type):
    response = client.post("/api/v1/cases/voice", headers=auth("patient-user-001"),
                           data={"lang": "hi"}, files={"audio": ("demo", b"audio", mime_type)})
    assert response.status_code == 200
    assert response.json()["fields"]["patient_id"] == "patient-001"


def test_voice_passes_media_type_without_codec_parameters_to_ai(client):
    from app.domain.ai import DeterministicFakeAI

    seen = []

    class CapturingAI(DeterministicFakeAI):
        def extract_voice(self, audio, language, mime_type, patient, drug_ids):
            seen.append(mime_type)
            return super().extract_voice(audio, language, mime_type, patient, drug_ids)

    previous = client.app.state.ai
    client.app.state.ai = CapturingAI()
    try:
        response = client.post("/api/v1/cases/voice", headers=auth("patient-user-001"),
                               data={"lang": "en"},
                               files={"audio": ("demo.webm", b"audio", "audio/webm;codecs=opus")})
    finally:
        client.app.state.ai = previous
    assert response.status_code == 200
    assert seen == ["audio/webm"]


@pytest.mark.parametrize("field", ["patient_id", "drug_id", "requested_qty",
                                    "household_supply_days", "attempted_at"])
@pytest.mark.parametrize("route", ["/cases", "/cases/voice/confirm"])
def test_case_routes_reject_null_required_field(client, route, field):
    fields = {"patient_id": "patient-001", "drug_id": "metformin", "requested_qty": 30,
              "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z"}
    fields[field] = None
    body = fields if route == "/cases" else {"fields": fields, "transcript": "दवा नहीं मिली।"}
    response = client.post("/api/v1" + route, headers=auth("patient-user-001"), json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert field in response.json()["error"]["message"]
