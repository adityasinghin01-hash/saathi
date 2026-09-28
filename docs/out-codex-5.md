Implemented B14 and B15. The proposed additive forecast is behind `DEMAND_RULE=calibrated`; the default remains `max`. The formula, held-out results, and limitations are in [notes-codex.md](/Users/aditya/dev/refill-loop/docs/notes-codex.md).

The combined rule had the lowest MAE in baseline, false reports, and long stockout. Dispensing-only did better on MAE with stale prescriptions and the enrolment gap; prescription-only generally prevented more unmet days, with substantially more overstock and false alerts. Full results are in [forecast.md](/Users/aditya/dev/refill-loop/backend/eval/results/forecast.md).

Gemini now retries 429/503 with bounded backoff, then marks deterministic API responses `ai_source: "fallback"`. The opt-in live test returned **403 PERMISSION_DENIED**; all 30 live extraction calls failed, so no live accuracy claim is made.

Verification: **66 passed, 1 skipped**; `ruff check app tests eval` passed. `ruff format --check` found 28 existing style differences, so I left formatting unchanged. No commit, push, or deploy.