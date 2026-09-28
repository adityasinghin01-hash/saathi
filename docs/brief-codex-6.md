Continue as backend engineer (network allowed). Read docs/CONTRACT.md "v0.4" first. Claude reviewed round 5: tests 66 passed/1 skipped verified; calibrated rule REJECTED as default (keep DEMAND_RULE=max, keep the code).

Claude's live retest of Gemini (29 Sep): the API key is valid (model list works). Your "403" came from the Vertex/ADC path — this Mac has personal gcloud ADC, which is NOT meant for this app. With the key: gemini-3.8-flash, 3.7-flash, 3.5-flash, flash-latest all returned 503 high-demand; gemini-2.5-flash is 404 (closed to new users); gemini-3.1-flash-lite answered once after ~15 s. Your SDK timeout is 2.5 s, so even that success would have been thrown away.

B16 — Make live Gemini actually usable:
1. Vertex/ADC only when env GEMINI_USE_VERTEX=1 (default off). Default = API key only.
2. Model fallback list from env GEMINI_MODELS (comma-separated), default "gemini-3.8-flash,gemini-3.1-flash-lite,gemini-3.5-flash". Per call: try models in order, 1 attempt each on 429/503, per-request timeout 20 s, whole call budget 40 s, then deterministic fallback with ai_source "fallback". Record which model answered (response field `ai_model` when ai_source is "gemini").
3. Every AI-touched response carries ai_source ("gemini"|"fake"|"fallback"): voice extraction AND transfer draft.
4. Run the opt-in live test and the 30-transcript Hindi extraction eval live (retry the whole eval up to 3 times over ~10 min if everything is 503). Record REAL numbers (per-field accuracy, calls ok/failed, which model, latency) in docs/notes-codex.md. If still all failures, say so plainly.

B17 — Explain a suspicious eval result: in B14's table, dispensing_only, calibrated and combined give IDENTICAL baseline numbers (unmet 227.58, stockout 4.92, lead 7.00). Find out why (e.g. no method ever crosses the alert threshold, or a bug). Fix it if it is a bug; either way write the cause in notes-codex.md.

B18 — API examples: POST /stock with {facility_id, drug_id, on_hand} returns 422 "Invalid stock quantities". Make docs/api-examples.md show a VALID stock call (fix backend/scripts/dump_api_examples.py to send the body the API really needs, e.g. batches summing to on_hand) and regenerate docs/api-examples.md with `DEMO_MODE=1 .venv/bin/python scripts/dump_api_examples.py`. Every example must be HTTP 2xx except the deliberate 404 at the end. Also add examples for: a transfer draft that returns no_feasible_transfer, POST /cases/{id}/cancel, and GET /cases as patient-user-001.

B19 — Deploy readiness (do NOT deploy): render.yaml for the backend (Python 3.11, uvicorn start command, DEMO_MODE=1, GEMINI_API_KEY as a secret env var with no value), CORS origins from env ALLOWED_ORIGINS (comma-separated; keep localhost:3000 default), seeds on startup if empty. Health check path /api/v1/health.

Rules: edit only backend/ and the two docs named (notes-codex.md, api-examples.md via the script). Never print or log the key. ruff clean; full pytest green; paste the real final pytest line. No commit, push, deploy.
