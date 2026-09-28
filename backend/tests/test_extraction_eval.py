import json

from eval.extraction_eval import CORPUS, evaluate_fake, evaluate_live, score_case


def test_corpus_is_30_distinct_labeled_transcripts():
    assert len(CORPUS) == 30
    assert len({case["transcript"] for case in CORPUS}) == 30
    assert any(case["gold"]["negated"] for case in CORPUS)
    assert any(not case["gold"]["negated"] for case in CORPUS)
    assert all(case["gold"]["strength"] and case["gold"]["facility"] for case in CORPUS)


def test_scoring_marks_unsupported_fields_missing_and_negation_errors():
    case = CORPUS[0]
    prediction = {"fields": {"drug_id": case["gold"]["medicine"],
                             "requested_qty": case["gold"]["requested_qty"],
                             "household_supply_days": case["gold"]["household_supply_days"],
                             "attempted_at": case["gold"]["date"] + "T09:00:00Z"},
                  "transcript": "Synthetic demo transcription of a refill request."}
    scores = score_case(case, prediction)
    assert scores["medicine"] is True
    assert scores["facility"] is False
    assert scores["received_qty"] is False
    assert scores["negated"] is (not case["gold"]["negated"])


def test_scoring_accepts_null_attempted_date_from_safe_fallback():
    case = CORPUS[0]
    prediction = {"fields": {"attempted_at": None}, "transcript": ""}
    assert score_case(case, prediction)["date"] is False


def test_fake_evaluation_reports_latency_accuracy_and_zero_provider_cost():
    result = evaluate_fake()
    assert result["samples"] == 30
    assert set(result["field_accuracy"]) == {
        "medicine", "strength", "facility", "date", "requested_qty",
        "received_qty", "household_supply_days", "negated"
    }
    assert result["estimated_cost_usd"] == 0
    assert result["latency_ms_mean"] >= 0
    assert result["negation_errors"] > 0


def test_live_text_path_uses_schema_and_usage_for_cost(monkeypatch):
    class Models:
        def generate_content(self, **kwargs):
            assert kwargs["config"].response_json_schema["required"] == [
                "transcript", "not_a_refill_report", "fields"]
            payload = {"transcript": "Refill unavailable", "not_a_refill_report": False,
                       "fields": {
                "drug_id": "metformin", "requested_qty": 30,
                "household_supply_days": 0, "attempted_at": "2026-09-28T09:00:00Z"}}
            usage = type("Usage", (), {"prompt_token_count": 100,
                                        "candidates_token_count": 20})()
            return type("Response", (), {"text": json.dumps(payload),
                                          "usage_metadata": usage})()

    monkeypatch.setattr("app.domain.ai.genai.Client",
                        lambda **kwargs: type("Client", (), {"models": Models()})())
    monkeypatch.setenv("GEMINI_INPUT_USD_PER_MILLION", "1")
    monkeypatch.setenv("GEMINI_OUTPUT_USD_PER_MILLION", "2")
    result = evaluate_live("secret")
    assert result["failed_calls"] == 0
    assert result["successful_calls"] == 30
    assert result["models_answered"] == {"gemini-3.8-flash": 30}
    assert result["input_tokens"] == 3000
    assert result["output_tokens"] == 600
    assert result["estimated_cost_usd"] == 0.0042
