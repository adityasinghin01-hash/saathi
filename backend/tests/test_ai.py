import json
import os

import httpx
import pytest

from app.domain.ai import (
    DeterministicFakeAI,
    GeminiDraftAI,
    UnsafeAIOutput,
    contains_medical_advice,
    select_draft_ai,
)


class StubModels:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return type("Response", (), {"text": self.text})()


class StubClient:
    def __init__(self, text):
        self.models = StubModels(text)


@pytest.mark.parametrize("status", [429, 503])
def test_gemini_tries_each_model_once_on_transient_error(status):
    from google.genai import errors

    from app.domain.ai import AIUnavailable

    class BusyModels:
        def __init__(self):
            self.calls = []

        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            error = errors.ClientError if status == 429 else errors.ServerError
            raise error(status, {"error": "busy"})

    models = BusyModels()
    adapter = GeminiDraftAI(type("Client", (), {"models": models})(), ["first", "second", "third"])
    with pytest.raises(AIUnavailable):
        adapter.transfer_rationale({"requested_qty": 30}, {"name": "Depot"}, 5)
    assert [call["model"] for call in models.calls] == ["first", "second", "third"]
    assert all(call["config"].http_options.timeout <= 20_000 for call in models.calls)


def test_gemini_does_not_retry_nontransient_error(monkeypatch):
    from google.genai import errors

    from app.domain.ai import AIUnavailable

    monkeypatch.setattr("app.domain.ai.time.sleep", lambda seconds: pytest.fail("unexpected retry"))

    class BadModels:
        calls = 0

        def generate_content(self, **kwargs):
            self.calls += 1
            raise errors.ClientError(400, {"error": "bad request"})

    models = BadModels()
    adapter = GeminiDraftAI(type("Client", (), {"models": models})(), ["first", "second"])
    with pytest.raises(AIUnavailable):
        adapter.transfer_rationale({"requested_qty": 30}, {"name": "Depot"}, 5)
    assert models.calls == 1


def test_gemini_voice_sends_audio_with_strict_schema_and_returns_contract_fields():
    client = StubClient(json.dumps({"transcript": "The refill was unavailable.",
                                    "not_a_refill_report": False,
                                    "fields": {"drug_id": "metformin", "requested_qty": 30,
                                               "household_supply_days": 0,
                                               "attempted_at": "2026-09-28T09:00:00Z"}}))
    adapter = GeminiDraftAI(client, "gemini-2.5-flash")
    result = adapter.extract_voice(b"audio", "en", "audio/ogg", {"id": "patient-001"},
                                   ["metformin", "amlodipine"])
    assert result["fields"] == {"patient_id": "patient-001", "drug_id": "metformin",
                                "requested_qty": 30, "household_supply_days": 0,
                                "attempted_at": "2026-09-28T09:00:00Z"}
    assert result["transcript"] == "The refill was unavailable."
    assert result["missing"] == []
    assert result["not_a_refill_report"] is False
    assert result["ai_source"] == "gemini"
    assert result["ai_model"] == "gemini-2.5-flash"
    call = client.models.calls[0]
    assert call["model"] == "gemini-2.5-flash"
    assert call["contents"][1].inline_data.mime_type == "audio/ogg"
    assert call["contents"][1].inline_data.data == b"audio"
    schema = call["config"].response_json_schema
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"transcript", "fields", "not_a_refill_report"}
    assert call["config"].response_mime_type == "application/json"


def test_gemini_voice_accepts_utc_offset_timestamp_from_real_audio_response():
    client = StubClient(json.dumps({"transcript": "कल दवा नहीं मिली।",
                                    "not_a_refill_report": False,
                                    "fields": {"drug_id": "metformin", "requested_qty": 30,
                                               "household_supply_days": 2,
                                               "attempted_at": "2026-09-28T20:34:44+00:00"}}))
    result = GeminiDraftAI(client, "gemini-3.1-flash-lite").extract_voice(
        b"wav", "hi", "audio/wav", {"id": "patient-003"}, ["metformin"])
    assert result["fields"]["attempted_at"] == "2026-09-28T20:34:44Z"
    assert result["ai_source"] == "gemini"


def test_gemini_voice_rejects_non_utc_offset_timestamp():
    client = StubClient(json.dumps({"transcript": "कल दवा नहीं मिली।",
                                    "not_a_refill_report": False,
                                    "fields": {"drug_id": "metformin", "requested_qty": 30,
                                               "household_supply_days": 2,
                                               "attempted_at": "2026-09-28T20:34:44+05:30"}}))
    with pytest.raises(UnsafeAIOutput):
        GeminiDraftAI(client, "gemini-3.1-flash-lite").extract_voice(
            b"wav", "hi", "audio/wav", {"id": "patient-003"}, ["metformin"])


def test_gemini_voice_rejects_medical_advice():
    client = StubClient(json.dumps({"transcript": "Take two tablets daily.",
                                    "not_a_refill_report": False,
                                    "fields": {"drug_id": "metformin", "requested_qty": 30,
                                               "household_supply_days": 0,
                                               "attempted_at": "2026-09-28T09:00:00Z"}}))
    adapter = GeminiDraftAI(client, "gemini-2.5-flash")
    with pytest.raises(UnsafeAIOutput):
        adapter.extract_voice(b"audio", "en", "audio/wav", {"id": "patient-001"}, ["metformin"])


def test_hindi_medicine_name_does_not_trigger_advice_filter():
    transcript = ("सोमवार 28 सितंबर को उदयपुर पीएचसी में अमलोडीपिन की 18 "
                  "गोलियां मांगी थी। दवा मिल गई थी। घर में 3 दिन की बची है।")
    assert contains_medical_advice(transcript) is False
    assert contains_medical_advice("दवा लो।") is True


def test_gemini_voice_rejects_blood_sugar_numbers():
    client = StubClient(json.dumps({"transcript": "My blood sugar is 180 and refill failed.",
                                    "not_a_refill_report": False,
                                    "fields": {"drug_id": "metformin", "requested_qty": 30,
                                               "household_supply_days": 0,
                                               "attempted_at": "2026-09-28T09:00:00Z"}}))
    adapter = GeminiDraftAI(client, "gemini-2.5-flash")
    with pytest.raises(UnsafeAIOutput):
        adapter.extract_voice(b"audio", "en", "audio/wav", {"id": "patient-001"}, ["metformin"])


def test_gemini_voice_rejects_unknown_drug():
    client = StubClient(json.dumps({"transcript": "Refill unavailable.",
                                    "not_a_refill_report": False,
                                    "fields": {"drug_id": "unknown", "requested_qty": 30,
                                               "household_supply_days": 0,
                                               "attempted_at": "2026-09-28T09:00:00Z"}}))
    adapter = GeminiDraftAI(client, "gemini-2.5-flash")
    with pytest.raises(UnsafeAIOutput):
        adapter.extract_voice(b"audio", "en", "audio/wav", {"id": "patient-001"}, ["metformin"])


def test_voice_partial_facts_keep_unspoken_values_null():
    client = StubClient(json.dumps({
        "transcript": "मेरी मेटफॉर्मिन की दवा नहीं मिली।",
        "not_a_refill_report": False,
        "fields": {"drug_id": "metformin", "requested_qty": None,
                   "household_supply_days": None, "attempted_at": None},
    }, ensure_ascii=False))
    result = GeminiDraftAI(client, "gemini-3.1-flash-lite").extract_voice(
        b"ogg", "hi", "audio/ogg", {"id": "patient-003"}, ["metformin"])
    assert result["fields"] == {
        "patient_id": "patient-003", "drug_id": "metformin", "requested_qty": None,
        "household_supply_days": None, "attempted_at": None,
    }
    assert result["missing"] == ["requested_qty", "household_supply_days", "attempted_at"]
    schema = client.models.calls[0]["config"].response_json_schema
    assert schema["properties"]["fields"]["properties"]["drug_id"]["anyOf"][1] == {"type": "null"}
    assert "Devanagari" in client.models.calls[0]["contents"][0]


def test_voice_non_refill_report_has_no_extracted_facts():
    client = StubClient(json.dumps({
        "transcript": "मुझे डॉक्टरों से शिकायत है।",
        "not_a_refill_report": True,
        "fields": {"drug_id": None, "requested_qty": None,
                   "household_supply_days": None, "attempted_at": None},
    }, ensure_ascii=False))
    result = GeminiDraftAI(client, "gemini-3.1-flash-lite").extract_voice(
        b"ogg", "hi", "audio/ogg", {"id": "patient-003"}, ["metformin"])
    assert result["not_a_refill_report"] is True
    assert result["missing"] == ["drug_id", "requested_qty", "household_supply_days",
                                 "attempted_at"]
    assert all(result["fields"][name] is None for name in result["missing"])


def test_voice_non_refill_report_rejects_invented_fact():
    client = StubClient(json.dumps({
        "transcript": "मुझे डॉक्टरों से शिकायत है।",
        "not_a_refill_report": True,
        "fields": {"drug_id": "metformin", "requested_qty": None,
                   "household_supply_days": None, "attempted_at": None},
    }, ensure_ascii=False))
    with pytest.raises(UnsafeAIOutput):
        GeminiDraftAI(client, "gemini-3.1-flash-lite").extract_voice(
            b"ogg", "hi", "audio/ogg", {"id": "patient-003"}, ["metformin"])


def test_hindi_voice_romanized_transcript_gets_devanagari_second_pass():
    class SequenceModels:
        def __init__(self):
            self.calls = []

        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                payload = {"transcript": "hamari tabiyat kharab hai doctor ji nahi sunte",
                           "not_a_refill_report": True,
                           "fields": {"drug_id": None, "requested_qty": None,
                                      "household_supply_days": None, "attempted_at": None}}
            else:
                payload = {"transcript": "हमारी तबीयत खराब है, डॉक्टर जी नहीं सुनते।"}
            return type("Response", (), {"text": json.dumps(payload, ensure_ascii=False)})()

    models = SequenceModels()
    adapter = GeminiDraftAI(type("Client", (), {"models": models})(), "gemini-3.1-flash-lite")
    result = adapter.extract_voice(b"ogg", "hi", "audio/ogg", {"id": "patient-003"},
                                   ["metformin"])
    assert result["transcript"] == "हमारी तबीयत खराब है, डॉक्टर जी नहीं सुनते।"
    assert result["not_a_refill_report"] is True
    assert result["fields"]["drug_id"] is None
    assert len(models.calls) == 2
    assert "inline_data" not in str(models.calls[1]["contents"])


def test_gemini_rationale_uses_only_engine_facts():
    client = StubClient('{"reason_code":"eligible_stock"}')
    adapter = GeminiDraftAI(client, "gemini-2.5-flash")
    result = adapter.transfer_rationale({"requested_qty": 30}, {"name": "Demo Store"}, 8.5)
    assert result["rationale"] == ("Synthetic demo draft: Demo Store has eligible stock for 30 units; "
                    "route distance 8.5 km. Officer approval required.")
    assert result["ai_source"] == "gemini"
    assert result["ai_model"] == "gemini-2.5-flash"
    assert client.models.calls[0]["config"].response_json_schema["additionalProperties"] is False


def test_gemini_rationale_uses_selected_route_fact():
    client = StubClient('{"reason_code":"shortest_eligible_route"}')
    adapter = GeminiDraftAI(client, "gemini-2.5-flash")
    assert adapter.transfer_rationale({"requested_qty": 30}, {"name": "Demo Store"}, 8.5)["rationale"] == (
        "Synthetic demo draft: Demo Store is the nearest eligible donor for 30 units "
        "at 8.5 km. Officer approval required."
    )


def test_select_draft_ai_uses_key_unless_vertex_explicitly_enabled(monkeypatch):
    clients = []

    def fake_client(**kwargs):
        clients.append(kwargs)
        return StubClient("{}")

    monkeypatch.setattr("app.domain.ai.genai.Client", fake_client)
    def forbidden_adc(**kwargs):
        pytest.fail("ADC was consulted without opt-in")

    monkeypatch.setattr("app.domain.ai.google.auth.default", forbidden_adc)
    ai = select_draft_ai({"GEMINI_MODELS": "first, second", "GEMINI_API_KEY": "secret"})
    assert isinstance(ai, GeminiDraftAI)
    assert clients[-1]["api_key"] == "secret"
    assert ai.models == ["first", "second"]
    monkeypatch.setattr("app.domain.ai.google.auth.default", lambda **kwargs: (object(), "adc-project"))
    vertex = select_draft_ai({"GEMINI_USE_VERTEX": "1", "GEMINI_API_KEY": "secret"})
    assert isinstance(vertex, GeminiDraftAI)
    assert clients[-1]["vertexai"] is True
    assert isinstance(select_draft_ai({}), DeterministicFakeAI)


def test_default_model_order_and_request_budget():
    from google.genai import errors

    from app.domain.ai import DEFAULT_MODELS

    class BusyThenSuccess:
        def __init__(self):
            self.calls = []

        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                raise errors.ServerError(503, {"error": "busy"})
            return type("Response", (), {"text": '{"reason_code":"eligible_stock"}'})()

    models = BusyThenSuccess()
    adapter = GeminiDraftAI(type("Client", (), {"models": models})(), DEFAULT_MODELS)
    result = adapter.transfer_rationale({"requested_qty": 30}, {"name": "Depot"}, 5)
    assert result["ai_model"] == DEFAULT_MODELS[1]
    assert [call["model"] for call in models.calls] == list(DEFAULT_MODELS[:2])


def test_gemini_tries_next_model_after_transport_timeout():
    class TimeoutThenSuccess:
        def __init__(self):
            self.calls = []

        def generate_content(self, **kwargs):
            self.calls.append(kwargs["model"])
            if len(self.calls) == 1:
                raise httpx.ReadTimeout("timed out")
            return type("Response", (), {"text": '{"reason_code":"eligible_stock"}'})()

    models = TimeoutThenSuccess()
    adapter = GeminiDraftAI(type("Client", (), {"models": models})(), ["first", "second"])
    result = adapter.transfer_rationale({"requested_qty": 30}, {"name": "Depot"}, 5)
    assert result["ai_model"] == "second"
    assert models.calls == ["first", "second"]


@pytest.mark.skipif(os.getenv("RUN_LIVE_GEMINI") != "1", reason="opt-in live Gemini test")
def test_live_gemini_transfer_rationale():
    ai = select_draft_ai()
    if isinstance(ai, DeterministicFakeAI):
        pytest.skip("No Gemini credentials configured")
    result = ai.transfer_rationale({"requested_qty": 30}, {"name": "Synthetic Depot"}, 5.0)
    assert "Synthetic Depot" in result["rationale"]
    assert "30 units" in result["rationale"]
    assert "5.0 km" in result["rationale"]
    assert result["ai_source"] == "gemini"
    assert result["ai_model"] in ai.models
