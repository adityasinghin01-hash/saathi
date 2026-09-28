# Refill Loop backend

Synthetic demo data only.

Requires Python 3.11 or newer. From the repository root:

```sh
python3.11 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e 'backend[dev]'
cd backend
.venv/bin/uvicorn app.main:app --reload
```

Run checks from `backend/`:

```sh
.venv/bin/python -m pytest -q
.venv/bin/ruff check app tests
```

The local SQLite database defaults to `backend/refill_loop.db` when started from `backend/`.
Set `DATABASE_URL` to another SQLite URL for another location.

## Gemini drafts

The app uses `GEMINI_API_KEY` and the Gemini Developer API by default. Vertex ADC is used
only when `GEMINI_USE_VERTEX=1`; `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` can
override its project and `global` location. Set `GEMINI_MODELS` to choose the ordered,
comma-separated fallback models. Each model gets one request on HTTP 429/503, with a
20-second request timeout and a 40-second total budget. With no configured credential,
the app uses its deterministic synthetic fake. Tests inject that fake explicitly.

Voice uploads accept `audio/webm`, `audio/ogg`, `audio/mp4`, `audio/mpeg`, `audio/wav`,
`audio/x-wav`, and `audio/wave`, with or without codec parameters and with `lang=hi` or `lang=en`.
Extraction returns fields and a transcript for user confirmation; it does not save a case.
Provider failures use marked deterministic fallback for voice. Invalid or unsafe model output is rejected.
Transfer rationales use only validated engine facts, and provider failures use the safe
deterministic rationale.

Run the opt-in live Vertex or API key check only when desired:

```sh
RUN_LIVE_GEMINI=1 .venv/bin/python -m pytest -q tests/test_ai.py::test_live_gemini_transfer_rationale
```

## Demo and deployment configuration

`DEMO_MODE=1` enables `POST /api/v1/demo/reset` for demo users; all other values disable it.
Reset deletes local records and restores the deterministic synthetic seed. The named Ramesh
scenario endpoint returns the IDs needed for the end-to-end story. With a running local server:

```sh
DEMO_MODE=1 .venv/bin/uvicorn app.main:app --port 8000
.venv/bin/python scripts/play_ramesh.py --base-url http://127.0.0.1:8000
```

Environment variables:

| Name | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy SQLite URL; defaults to `backend/refill_loop.db` locally and `/app/data/refill_loop.db` in the container. Use persistent storage for a durable deployment. |
| `GEMINI_API_KEY` | Gemini Developer API credential; used by default. |
| `GEMINI_MODELS` | Ordered Gemini fallback models; defaults to `gemini-3.8-flash,gemini-3.1-flash-lite,gemini-3.5-flash`. |
| `GEMINI_USE_VERTEX` | Set to `1` to opt into Vertex application default credentials; otherwise the API key is used. |
| `DEMO_MODE` | Exactly `1` enables the destructive synthetic demo reset route. |
| `ALLOWED_ORIGINS` | Comma-separated allowed browser origins; defaults to `http://localhost:3000`. |
| `EVALUATION_RESULTS_DIR` | Optional directory for `forecast.json` and `extraction.json`; defaults to `backend/eval/results`. |

The container listens on port 8080. Build from `backend/` with `docker build -t refill-loop-backend .`.
`GET /api/v1/evaluation/summary` serves saved offline evaluation results to district officers.
The default SQLite database inside a container is ephemeral unless `/app/data` is mounted on
persistent storage. Demo login and reset are for synthetic demonstration, not production auth.

For a Render Blueprint, set the Blueprint path to `backend/render.yaml`. It starts one
Python 3.11 web service, sets `DEMO_MODE=1`, and prompts for `GEMINI_API_KEY` as a secret.
Startup seeds the SQLite database only when it is empty. Configure `ALLOWED_ORIGINS` in
the service environment for the frontend origin. The health check is `/api/v1/health`.

## Offline evaluation

From `backend/`:

```sh
PYTHONPATH=. .venv/bin/python -m eval.forecast_eval
PYTHONPATH=. .venv/bin/python -m eval.extraction_eval
```

The first command regenerates `eval/results/forecast.json` and `forecast.md` from an
independent patient-level simulator. `eval/forecast.ipynb` runs the same experiment.
The second scores 30 hand-authored synthetic Hindi/Hinglish transcripts. Without
`GEMINI_API_KEY`, it evaluates the deterministic fake and records live evaluation as
`not_run_no_api_key`. With a key, it also runs text-only Gemini extraction against the
product JSON schema. This does not measure audio transcription quality. The fake ignores
the transcript, so its matching fields are incidental, not evidence of extraction skill.

For live audio evaluation with a configured `GEMINI_API_KEY`, run
`PYTHONPATH=. .venv/bin/python -m eval.audio_eval`. It posts the twelve labeled synthetic
TTS WAV clips through the real `/cases/voice` TestClient route and writes
`eval/results/audio.json`. The first-pass results and paced retries are explained in
`eval/results/audio.md`. Put optional real recordings in `eval/audio/real/` following its
README; never add gold JSON unless the recorder supplies the expected fields. The evaluator
reports unlabeled transcripts and fields for review by ear.

Live estimated cost is calculated from returned token counts only when both
`GEMINI_INPUT_USD_PER_MILLION` and `GEMINI_OUTPUT_USD_PER_MILLION` are set to verified
rates for the selected model; otherwise cost is `null`. The fake has no provider cost.
