# Codex backend handoff

## District overview cache and browser audio types (29 Sep 2026)

- `GET /api/v1/district/overview` caches computed rows in the SQLite store by district, horizon, and demand rule. Writes to facility, drug, patient, prescription, stock snapshot, daily stock, stockout day, dispensing, case, or transfer records clear the cache; demo reset clears it too. Authorization and district scope checks still run on every request. The cache is per app process, consistent with the local single-process SQLite demo.
- On the same seeded in-memory app through TestClient, three calls before the change took **4,746.4 ms cold, 3,064.5 ms, 3,125.7 ms**. After the change they took **4,082.3 ms cold, 2.2 ms, 1.8 ms**. No local server was listening on port 8000 for a comparable curl run. The first call after startup or invalidation still recomputes the rows.
- Voice upload validation now compares the media type without codec parameters and passes that normalized type to the AI adapter. Accepted types include WebM, Ogg, MP4, MPEG, WAV, and x-wav (plus the previously accepted wave alias). Tests cover Chrome's `audio/webm;codecs=opus`, Safari-compatible `audio/mp4`, the other allowed types, and unsupported audio rejection.
- Focused red tests reproduced both bugs before implementation. Final `.venv/bin/python -m ruff check app tests eval scripts`: `All checks passed!`. Full `.venv/bin/python -m pytest -q` final line: `119 passed, 1 skipped, 1 warning in 79.76s (0:01:19)`. No commit, push, or deployment was performed.

## Round 8 seed realism follow-up (29 Sep 2026)

- Replaced the blanket metformin zero-stock seed with PHC-specific quantities: Sundarpur 0, Nayagaon 136, Amarpur 280, Shantipur 28, Navgram 110, and Udaypur 25 tablets. The district store now holds 1,500 metformin tablets, matching its other seeded drugs. Newly stocked PHCs have nonzero batches and 90-day stock/dispensing history; Sundarpur retains its injected stockout history.
- Amarpur and Shantipur sit at about 14 days of metformin cover; Navgram and Udaypur are low. The other seeded drugs remain mixed, with four low PHC rows and the rest okay. Nayagaon is the only PHC with at least 30 metformin tablets above its 14-day safety stock.
- The transfer selector now considers PHCs as donors; the district store remains visible with stock in the district overview. The focused seed test and existing test that removes Nayagaon's stock confirm that the district store is not drafted as the Ramesh donor.
- `play_ramesh.py` completed reset, report, verify, draft from `phc-2`, approve, dispatch, receive, supply, and close using its own `call` function with `urlopen` routed to an in-process TestClient. A separate API run returned `no_feasible_transfer` with `needs_split_or_supply` for 100,000 units. A direct Uvicorn listener could not bind to `127.0.0.1` in this sandbox (`operation not permitted`).
- `DEMO_MODE=1 .venv/bin/python scripts/dump_api_examples.py` regenerated `docs/api-examples.md` with the `phc-2` draft and no-feasible example. `.venv/bin/python -m ruff check app tests eval scripts`: `All checks passed!`. Full `.venv/bin/python -m pytest -q` final line: `83 passed, 1 skipped, 1 warning in 57.04s`. No commit, push, or deployment was performed.
- The existing `backend/refill_loop.db` still has the old metformin seed and four cases. `seed_if_empty` leaves a populated database alone. I left that database intact; the demo reset route will load the new seed when those cases can be discarded.

## B20–B21 live audio and submission drafts (29 Sep 2026)

- `POST /api/v1/cases/voice` already passed the uploaded raw bytes and MIME type to `GeminiDraftAI.extract_voice`; the adapter uses `types.Part.from_bytes` as an inline audio part. The existing byte-for-byte adapter test confirms the path. The deterministic `ai_source: "fallback"` remains in place for provider failures.
- The first real audio test exposed a parser bug: Gemini returned UTC `attempted_at` with `+00:00`, but validation accepted only `Z`, causing HTTP 422. The parser now accepts UTC offsets of zero, normalizes to `Z`, and rejects non-UTC offsets. Focused red/green tests cover both cases.
- Twelve short labeled synthetic Hindi TTS WAV clips and per-clip gold JSON files are in `backend/eval/audio/synthetic/`. Eight were made with `gemini-3.8-flash-tts`, four with `gemini-3.8-flash-lite-tts` after rate limits. They cover four seeded medicines, date words, quantities, days left, two positive receipt statements, and two Hinglish scripts. None is a real patient recording.
- `backend/eval/audio_eval.py` posts all clips through TestClient with live Gemini and writes `backend/eval/results/audio.json`. First pass: 12/12 HTTP 200, 9/12 live Gemini (`gemini-3.1-flash-lite`), three provider fallbacks, 14.85 s mean latency across all calls and 9.46 s across live answers. Among live answers, medicine, quantity and household days were each 9/9; attempted date was 8/9. `s08` transcript had the right September 27 date but extracted September 28. All wrong fields and per-clip latencies are in `audio.md`. The two positive clips succeeded on separate paced live retries; `s12` still fell back. No real recordings were present.
- `backend/eval/audio/real/README.md` gives the anonymous `.m4a`/`.webm`/`.wav` format and under-20-second guidance. The evaluator reports unlabeled real transcripts and fields and only scores gold labels that Aditya supplies. `.m4a` is converted to WAV with `afconvert` on this Mac, because the installed `ffmpeg` binary cannot run on its CPU; a focused conversion test passes.
- A separate Ramesh demo-user check posted `s01.wav` as `patient-user-001` and received a live `gemini-3.1-flash-lite` answer in 8.73 s with the expected medicine, quantity, household days, and date. It is outside the twelve-clip accuracy denominator (`backend/eval/results/audio_ramesh_check.json`).
- Submission drafts are `docs/README-draft.md`, `docs/description-draft.md`, and `docs/video-script-draft.md`. Unverified browser integration and real-speech outcomes are marked `[VERIFY]`. No commit, push, or deployment was performed.

All records and fake AI responses are labelled **Synthetic demo data**. No real patient records were used. No commit, push, or deployment was performed.

## B10–B13 continuation (28 Sep 2026)

- B10: `backend/eval/forecast_eval.py` generates patient-level need independently of the product forecasts. It derives incomplete enrollment and stock-limited dispensing afterward. Exactly 48 of 80 patients are enrolled in the enrolment-gap scenario. Outside purchases remain in true medicine need but are absent from PHC requests and dispensing. False-report runs are paired with baseline need and stock; 407 false reports were generated across the 12 runs and none enters a forecast. The long-stockout scenario censors days 50–89 of the 90-day history, plus the common five-day stockout.
- B11: deterministic reset and named scenario endpoints added. A donor check found `phc-2` as the sole feasible PHC for Ramesh’s 30-unit metformin request. `scripts/play_ramesh.py` ran against local Uvicorn with `DEMO_MODE=1`: reset, report, verify, draft from `phc-2`, approve, dispatch, receive, supply, close all returned 200; the eight event statuses were printed in order.
- B12: container files, env documentation, CORS configuration, and district-only evaluation summary added. Docker was not built because the `docker` executable is unavailable in this environment.
- B13: 30 hand-authored Hindi/Hinglish synthetic transcripts and a scorer were added. The fake was run locally. No `GEMINI_API_KEY` was present, so live Gemini was not run; the stubbed live path is covered by a test. The harness is transcript-only and does not assess audio recognition. Facility and received quantity are absent from the product extraction schema, so they score zero. Strength is normalized from the predicted drug ID; negation is scored from the returned transcript.

### Verification

- `cd backend && .venv/bin/python -m pytest -q`: **56 passed, 1 skipped, 1 warning in 17.57s**. The skipped test is opt-in live Gemini; the warning is Starlette’s dependency deprecation warning.
- `cd backend && .venv/bin/ruff check app tests eval scripts`: **All checks passed!**
- The two evaluation JSON files and forecast notebook passed `python3 -m json.tool` parsing.
- No commit, push, or deployment was performed.

### Forecast evaluation

Synthetic demo data. Twelve seeded repetitions per scenario. MAE compares forecast units/day with independently generated total patient need, including outside purchases. False alerts and unmet patient-days use PHC requests; outside purchases are treated as filled elsewhere. A simulated order arrives after seven days and is sized to 130% of the forecast. False-alert rate is false alerts divided by all runs. Lead time is days from cutoff warning to true shortage, with missed warnings scored zero.

| Scenario | Method | MAE/day | False alert rate | Unmet patient-days | Lead days |
| --- | --- | ---: | ---: | ---: | ---: |
| baseline | dispensing_only | 4.98 | 0.000 | 227.58 | 7.00 |
| baseline | prescription_only | 24.07 | 0.333 | 3.33 | 12.58 |
| baseline | combined | 24.07 | 0.333 | 3.33 | 12.58 |
| enrolment_gap | dispensing_only | 4.11 | 0.000 | 237.58 | 6.67 |
| enrolment_gap | prescription_only | 4.04 | 0.000 | 237.58 | 6.67 |
| enrolment_gap | combined | 3.44 | 0.000 | 237.58 | 6.67 |
| stale_prescriptions | dispensing_only | 3.57 | 0.083 | 233.25 | 5.67 |
| stale_prescriptions | prescription_only | 59.42 | 0.333 | 25.17 | 11.42 |
| stale_prescriptions | combined | 59.42 | 0.333 | 25.17 | 11.42 |
| false_reports | dispensing_only | 4.98 | 0.000 | 227.58 | 7.00 |
| false_reports | prescription_only | 24.07 | 0.333 | 3.33 | 12.58 |
| false_reports | combined | 24.07 | 0.333 | 3.33 | 12.58 |
| outside_purchases | dispensing_only | 25.76 | 0.000 | 148.08 | 2.17 |
| outside_purchases | prescription_only | 23.76 | 0.750 | 0.00 | 22.08 |
| outside_purchases | combined | 23.76 | 0.750 | 0.00 | 22.08 |
| long_stockout | dispensing_only | 4.28 | 0.083 | 260.17 | 7.08 |
| long_stockout | prescription_only | 24.14 | 0.250 | 8.33 | 11.92 |
| long_stockout | combined | 24.14 | 0.250 | 8.33 | 11.92 |

Combined loses on hidden-demand MAE to dispensing-only in baseline, stale prescriptions, false reports, and long stockout. It has a higher false-alert rate than dispensing-only in those four scenarios and outside purchases. In the enrolment-gap scenario, combined has the lowest MAE. These results are simulator outcomes, not field effectiveness claims. Full methods and results are in `backend/eval/results/forecast.md` and `forecast.json`.

### Hindi/Hinglish extraction evaluation

Synthetic demo data. The deterministic fake ignores input transcripts; any correct fields are incidental. Provider cost for this fake run was zero. Measured mean call latency was 0.001 ms in-process, which is not a network latency estimate.

| Field | Fake accuracy |
| --- | ---: |
| medicine | 0.300 |
| strength | 0.300 |
| facility | 0.000 |
| date | 0.067 |
| requested_qty | 0.300 |
| received_qty | 0.000 |
| household_supply_days | 0.267 |
| negated | 0.500 |

Negation errors: **15/30**. Live result: **not_run_no_api_key**. Live estimated cost remains unreported until a real run returns token counts and verified per-token rates are supplied; the script does not guess model pricing. Full results are in `backend/eval/results/extraction.json`.

---

## Continuation with network access (28 Sep 2026)

- Installed `google-genai 1.75.0` and `google-auth 2.58.1` in `backend/.venv`; added them to `backend/pyproject.toml`. `pip check` returned `No broken requirements found.`
- `cd backend && .venv/bin/python -m ruff check app tests`: **All checks passed!** Ruff initially found 63 issues; fixed the existing style findings and replaced route-level `Depends(...)` defaults with a shared dependency singleton.
- `cd backend && .venv/bin/python -m pytest -q`: **44 passed, 1 skipped, 1 warning in 13.40s**. The skip is the opt-in live Gemini test. The warning is Starlette's `httpx`/`testclient` deprecation warning from a dependency.
- Uvicorn smoke on `127.0.0.1:8000` using a fresh SQLite file: `GET /api/v1/health` returned **200** and `{"status":"ok","label":"Synthetic demo data"}`; `GET /api/v1/district/overview` with `X-Demo-User: officer-1` returned **200**, valid JSON, and **28** facility/drug rows. Uvicorn shut down cleanly.
- B1–B6, B8, and B9 are checked in `docs/TASKS.md` after the passing suite and smoke test. B7 remains unchecked because the real provider did not pass its opt-in live test.

### B7 implementation and live limit

- The `DraftAI` boundary now selects Vertex AI through application default credentials, then `GEMINI_API_KEY`, then the deterministic fake. If both Vertex and API key are configured, a failed Vertex request retries through the API key. `GEMINI_MODEL` selects the model; the default is `gemini-2.5-flash`.
- Voice accepts webm, ogg, and wav with `hi` or `en`, sends inline audio to the Google Gen AI SDK with a strict JSON schema, validates the result, and leaves case creation to `/cases/voice/confirm`. The backend rejects direct English/Hindi medication instructions and blood-sugar numbers it detects at both voice confirmation and shared case creation; the text filter is conservative and is not a clinical safety classifier. Transfer rationale uses a model-selected reason code, then renders only engine-checked donor, quantity, and distance facts. Provider errors return JSON 503 for voice; transfer drafting uses the deterministic fact-only rationale.
- The local ADC resolves a project. `RUN_LIVE_GEMINI=1 .venv/bin/python -m pytest -q tests/test_ai.py::test_live_gemini_transfer_rationale` **failed**: Vertex rejected the request with a billing-enablement error for that project. This is an external project setup issue; the fake and SDK-boundary tests pass, but a live generated response remains unverified.
- No commit, push, or deploy was performed.

## Earlier handoff (before network access)

### Task status

| Task | Work in `backend/` | Verification status |
| --- | --- | --- |
| B1 | FastAPI application, Python 3.11 virtual environment, `pyproject.toml`, pytest/ruff configuration, health route, README. | Package installation blocked by sandbox DNS/network restriction. Installed `uv` and Python 3.12/3.13 binaries are incompatible with this CPU; Python 3.11 works. |
| B2 | `Store` interface, SQLModel/SQLite record store, Firestore adapter stub, persistence test. | Runtime test blocked by missing dependencies. |
| B3 | Seed 42: fictional Suryanagar district, 2 blocks, 6 PHCs and 1 store, 4 drugs, 60 patients and demo users, prescriptions, 90 days of dispensing, 3 censored stockout periods, batches and snapshots. | Determinism/idempotence check passed with an in-memory store. This is the only task box checked in `TASKS.md`. |
| B4 | Scoped case endpoints, state machine, verification branches, cancellation, append-only case events, supply stock deduction and dispensing records. | Endpoint tests written; execution blocked. |
| B5 | Manual stock snapshots; district rows with separate cohort and TSB dispensing forecasts, censored days, combined estimate, days left and warnings. | Pure cohort/censor/warning checks passed; endpoint execution blocked. |
| B6 | OR-Tools minimum cost flow chooses the shortest eligible single donor; 14-day donor reserve, batch expiry and quantity checks; draft, approval, rejection, dispatch, receipt, escalation. | Endpoint tests written; execution blocked. |
| B7 scope now | `DraftAI` interface and deterministic fake for voice extraction and transfer rationale. No real Gemini adapter. | Voice endpoint test written; execution blocked. B7 box left unchecked because real wiring is later. |
| B8 | `Idempotency-Key` replay and conflict handling for POSTs; `/sync/batch` with per-user `op_id` deduplication. Local process locks cover concurrent retries within one server process. | Endpoint tests written; execution blocked. |
| B9 | 22 tests cover each endpoint and the Ramesh report → verify → draft → approve → dispatch → receive → supply → close path. | Full suite could not start because pytest is unavailable. Box left unchecked. |

Implementation boxes other than B3 remain unchecked pending dependency installation and runtime verification.

## Run commands

From the repository root, with package network access:

```sh
python3.11 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e 'backend[dev]'
cd backend
.venv/bin/uvicorn app.main:app --reload
```

For checks from `backend/`:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check app tests
```

The default SQLite file is `backend/refill_loop.db`. `DATABASE_URL` overrides it. The demo header is `X-Demo-User`; `GET /api/v1/demo/users` lists choices.

## Test summary (28 Sep 2026)

- `python -m compileall -q backend/app backend/tests`: passed.
- Five direct pure-domain checks: passed (seed, state transitions, cohort calculation, warning thresholds, censored daily dispensing).
- `cd backend && .venv/bin/python -m pytest -q`: **not run**; exit 1, `No module named pytest`.
- `cd backend && .venv/bin/python -m ruff check app tests`: **not run**; exit 1, `No module named ruff`.
- `pip install -e 'backend[dev]'`: failed while fetching build dependencies; DNS resolution was unavailable (`No matching distribution found for setuptools>=68` after network retries). The full endpoint suite, SQLModel persistence, TSB and OR-Tools paths have therefore not been verified in this environment.

## Open questions for Claude

1. A `Transfer` has one `from_facility_id`, while minimum cost flow can split a request among donors. Should the contract allow several transfers for one case, or require one donor to cover the whole request?
2. Which case status and transfer status should follow rejection or cancellation after approval or dispatch? The contract defines no rejection transition for cases and no cancelled transfer status.
3. Is a separate cancellation endpoint wanted in the API table? This implementation adds `POST /cases/{id}/cancel` to expose the stated side exit.
4. What exact shape should offline `ops` use, and should one failed op stop later ops? The contract gives only `op_id`.
5. What district overview horizon and enrolled-dominant drug classification should be used beyond the synthetic demo?
6. What are the precise patient visibility rules for ASHAs, pharmacists and district officers? Is the demo user picker public?
7. What should a partial dispense do to case status and `received_qty`?
8. Does case `received_qty` count units received at the facility or units handed to the patient?

## Assumptions used in code

- Demo user picker is public; all other `any` endpoints except health require a selected demo user. Patient access is self only; ASHA access is assigned patients; pharmacist access is facility scoped; officer access is district scoped.
- District horizon is 30 days. All four seeded drugs use the documented enrolled-dominant `max` rule. Known stockout dates are omitted from the TSB series and daily records are aggregated by date.
- One transfer has one donor. A donor must alone cover the full request. Arrival is one day after draft; eligible batches expire later than 30 days after that arrival.
- A rejected transfer stays attached to a `transfer_drafted` case until the officer requests a replacement draft. A cancelled case cannot be dispatched or received later. Terminal cases cannot be cancelled retroactively.
- `supplied` means the full requested quantity was handed over in one action. Case `received_qty` counts units handed to the patient; supply deducts a new stock snapshot and adds a dispensing record.
- The fake voice extractor selects the first active prescription. ASHAs provide `patient_id` in multipart form data. Voice extraction alone never saves a case.
- Pharmacists record only `manual` stock snapshots in this demo.
- Offline ops use `{op_id, path, body}` where `path` names a supported POST route. Each op reports its own result or error. `Idempotency-Key` and `op_id` locks protect one local server process; multi-process atomicity needs a storage-level transaction in a later deployment task.

## Antigravity fix

- **Root cause:** The test `test_stock_available_supply_deducts_stock` expected a single dispensing record of 10 units. However, because of the partial supply feature (v0.2 decisions #7), the API correctly adds one `DispensingRecord` per supply call with the quantity handed over in that call (contract v0.2), which in this test were two separate calls for 1 and 9 units.
- **What changed:** Updated the test assertion in `backend/tests/test_cases.py` to check for the two separate dispensing records with quantities 1 and 9 instead of a single record with 10.
- **Final pytest summary line:** `29 passed, 1 warning in 11.86s`

## Proposed CONTRACT change (B14; awaiting Claude approval)

For facility `f`, drug `d`, and horizon `H` days, let `E` be patients with an active, staff-confirmed prescription for `d`, and `q_i` their prescribed units per day. For each patient, reconstruct covered days from dated, patient-attributed dispensing quantities, carrying unused units forward and capping each day's coverage at one prescribed day. Omit documented stockout dates from the observation window. Let `c_i` be covered days and `n_i` observed days from that patient's first attributed fill through the end of facility history. The facility prior is `p_f = sum(c_i) / sum(n_i)` over patients with attributed fills; when there are none, use `p_f = 1` because adherence is unidentifiable from anonymous dispensing. With shrinkage strength `k` days, `p_i = (c_i + k*p_f)/(n_i + k)`; a patient with no attributed fill gets `p_i = p_f`.

`calibrated_cohort_need = H * sum(i in E, q_i * p_i)`.

For each uncensored historical day `t`, define `U_t` as the sum of dispensing units with a non-null `patient_id` **outside** `E`. Anonymous fills are excluded from `U_t` because their enrolled share cannot be subtracted reliably. `dispensing_forecast_for_unenrolled_share = TSB(U_t, horizon=H)`, with zero days retained in the residual series. The proposed rule is:

`combined = calibrated_cohort_need + max(0, dispensing_forecast_for_unenrolled_share)`.

Thus enrolled fills contribute to PDC only, while identifiable unenrolled fills contribute to the residual only. This avoids counting the same fill in both terms. It also means facilities with only anonymous historical fills have an unestimated unenrolled residual. `DEMAND_RULE=calibrated` enables this rule; the default remains `DEMAND_RULE=max`, using the existing `max(cohort_need, dispensing_forecast)` behavior pending approval. The existing per-drug `dispensing_only` override still applies under `max`.

## B14 held-out evaluation (28 Sep 2026)

The independent patient simulator now emits attributed historical fills. The truth remains independently generated patient need before outside purchases. Shrinkage candidates `k = 0, 10, 30, 60` were scored on repetitions 1000–1007 across all six scenarios; `k = 60` had the lowest training MAE/day (13.25; other candidates 13.35, 13.31, 13.28). The table below uses separate repetitions 0–11. MAE is units/day against all true need. False-alert rate is per run. Unmet patient-days and stockout days use PHC requests; overstock is mean daily on-hand units above 30 days of true patient need. Lead days is the mean for runs with real shortages, with missed alerts scored zero. A replenishment order arrives on day 7 and targets 130% of forecast.

| Scenario | Method | MAE/day | False alert rate | Unmet patient-days | Overstock units | Stockout days | Lead days |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | dispensing_only | 4.98 | 0.000 | 227.58 | 0.25 | 4.92 | 7.00 |
| baseline | prescription_only | 24.07 | 0.333 | 3.33 | 389.19 | 0.17 | 12.58 |
| baseline | calibrated | 6.07 | 0.000 | 227.58 | 0.00 | 4.92 | 7.00 |
| baseline | combined | 3.81 | 0.000 | 227.58 | 0.02 | 4.92 | 7.00 |
| enrolment_gap | dispensing_only | 4.11 | 0.000 | 237.58 | 0.03 | 5.08 | 6.67 |
| enrolment_gap | prescription_only | 4.04 | 0.000 | 237.58 | 0.00 | 5.08 | 6.67 |
| enrolment_gap | calibrated | 23.52 | 0.000 | 629.08 | 0.00 | 13.58 | 2.58 |
| enrolment_gap | combined | 4.27 | 0.000 | 237.58 | 0.00 | 5.08 | 6.67 |
| stale_prescriptions | dispensing_only | 3.57 | 0.083 | 233.25 | 0.97 | 5.42 | 5.67 |
| stale_prescriptions | prescription_only | 59.42 | 0.333 | 25.17 | 1461.91 | 0.83 | 11.42 |
| stale_prescriptions | calibrated | 15.17 | 0.333 | 25.17 | 186.26 | 0.83 | 11.42 |
| stale_prescriptions | combined | 17.51 | 0.333 | 25.17 | 236.45 | 0.83 | 11.42 |
| false_reports | dispensing_only | 4.98 | 0.000 | 227.58 | 0.25 | 4.92 | 7.00 |
| false_reports | prescription_only | 24.07 | 0.333 | 3.33 | 389.19 | 0.17 | 12.58 |
| false_reports | calibrated | 6.07 | 0.000 | 227.58 | 0.00 | 4.92 | 7.00 |
| false_reports | combined | 3.81 | 0.000 | 227.58 | 0.02 | 4.92 | 7.00 |
| outside_purchases | dispensing_only | 25.76 | 0.000 | 148.08 | 0.00 | 6.00 | 2.17 |
| outside_purchases | prescription_only | 23.76 | 0.750 | 0.00 | 674.19 | 0.00 | 22.08 |
| outside_purchases | calibrated | 25.81 | 0.000 | 148.08 | 0.00 | 6.00 | 2.17 |
| outside_purchases | combined | 24.14 | 0.000 | 111.33 | 0.00 | 4.58 | 3.33 |
| long_stockout | dispensing_only | 4.28 | 0.083 | 260.17 | 0.21 | 5.67 | 7.08 |
| long_stockout | prescription_only | 24.14 | 0.250 | 8.33 | 393.46 | 0.17 | 11.92 |
| long_stockout | calibrated | 5.20 | 0.000 | 319.58 | 0.00 | 7.00 | 5.83 |
| long_stockout | combined | 2.81 | 0.083 | 133.75 | 0.61 | 2.83 | 9.42 |

The combined rule has the lowest MAE in baseline, false reports, and long stockout, but dispensing-only has lower MAE in stale prescriptions and enrolment gap. Prescription-only minimizes unmet days in baseline, stale prescriptions, outside purchases, and long stockout, at a large overstock and false-alert cost. Calibrated alone has very low overstock, but the enrolment-gap scenario produces 629.08 unmet days versus 237.58 for dispensing-only and combined. Combined retains false alerts in stale prescriptions (0.333) and has higher overstock there (236.45 units) than dispensing-only (0.97). Outside purchases depress clinic-derived PDC even when true adherence remains high, so combined still has 24.14 MAE/day there. False reports do not affect any forecast inputs, so that row duplicates baseline results. Full machine-readable results: `backend/eval/results/forecast.json`; full table: `backend/eval/results/forecast.md`.

## B15 Gemini resilience (28 Sep 2026)

The Gemini adapter retries HTTP 429/503 at most three total attempts with exponential delay (0.2, 0.4 seconds before jitter); each SDK request has a 2.5-second timeout and its internal retry is limited to one attempt. When Vertex ADC and API-key clients are both available, their attempt budgets are one plus two, still three total. A provider failure falls back to the deterministic fake in voice extraction and transfer drafting, and API output marks `ai_source: "fallback"`. Local `.env` is loaded at backend startup without replacing already set environment values; the key is never logged.

The opt-in live transfer-rationale test was attempted once and failed: the provider returned HTTP **403 PERMISSION_DENIED**, not 503. The live 30-transcript extraction evaluation was attempted once using `gemini-3.8-flash`: **30/30 calls failed** (`ClientError`), with zero input/output tokens and no cost estimate. Those are failed live results, not model accuracy scores; the recorded zero field accuracy follows from missing predictions. Local deterministic fallback remains available. Standard suite after B14/B15: `66 passed, 1 skipped, 1 warning in 25.51s`; `ruff check app tests eval`: `All checks passed!`. The opt-in live test is the skipped test in the standard suite and fails as described when enabled. `ruff format --check` was also tried and found 28 files outside the repository's existing formatting style; no formatting sweep was applied.

## B16–B19 continuation (29 Sep 2026)

The B15 live failure followed the local Vertex ADC path. B16 now selects Gemini Developer API key access by default and consults Vertex ADC only with `GEMINI_USE_VERTEX=1`. `GEMINI_MODELS` controls an ordered list, defaulting to `gemini-3.8-flash,gemini-3.1-flash-lite,gemini-3.5-flash`. The adapter sends one request per model on HTTP 429/503 or transport timeout, with a 20-second per-request timeout and a 40-second overall budget. Successful voice extraction and transfer drafts carry `ai_source: "gemini"` and `ai_model`; deterministic local output carries `ai_source: "fake"`, and provider failure or an engine-only no-feasible result carries `ai_source: "fallback"`. The API key is not logged. The opt-in live rationale test passed with the API key path: `1 passed, 1 warning in 3.89s`.

The 30-transcript **live text extraction** run completed with **26 successful calls and 4 failed calls**. Answering models: `gemini-3.1-flash-lite` **25**, `gemini-3.8-flash` **1**; `gemini-3.5-flash` answered **0**. Failure HTTP codes were **503, 503, 503, 504**. Mean end-to-end latency across all 30 calls was **5,887.902 ms**. The run used **2,662 input tokens** and **3,060 output tokens**; estimated cost is **unknown** because verified token rates were not supplied. Since the run had successes, the whole-eval all-503 retry condition did not apply. Accuracy below uses **all 30** transcripts as denominator, so failed calls count as incorrect fields:

| Field | Live accuracy |
| --- | ---: |
| medicine | 0.867 |
| strength | 0.867 |
| facility | 0.000 |
| date | 0.867 |
| requested_qty | 0.833 |
| received_qty | 0.000 |
| household_supply_days | 0.867 |
| negated | 0.967 |

There was **1 negation error**. Facility and received quantity are absent from the product extraction schema, so their zero scores reflect unsupported fields. Strength is inferred from the extracted drug ID. This is a transcript-only eval; it does not assess audio transcription. The machine-readable result is `backend/eval/results/extraction.json`.

### B17 baseline metric diagnosis

The three B14 baseline methods have different forecasts and replenishment order quantities. In all 12 seeded repetitions, however, dispensing-only, calibrated, and combined make the same cutoff decision: 8 alerts and 4 missed alerts. For the 8 alerted runs, the different orders all cover demand after the seven-day delivery. The only alerted unmet demand occurs before that delivery (22 and 18 units in two runs). The 4 unalerted runs have the same initial stock and true requests and therefore the same shortages (750, 613, 614, and 714 units). Their mean is exactly **227.58 unmet patient-days**, with **4.92 stockout days** and **7.00 lead days**. This equality is an outcome of the simulator's threshold and supply rule, not a code bug. No forecast rule was changed; `DEMAND_RULE=max` remains the default and calibrated remains available only by explicit setting.

### B18 and B19

`scripts/dump_api_examples.py` now sends a stock snapshot with a batch summing to `on_hand`, and it asserts each documented response is 2xx except the deliberate final 404. The regenerated examples include a patient-scoped case list, cancellation, and a no-feasible transfer. The script exposed that `/sync/batch` rejected the v0.4 relative `/cases` path; the handler now accepts that path, and the regenerated sync example reports `applied`.

`backend/render.yaml` defines a Python 3.11 web service with a uvicorn start command, `DEMO_MODE=1`, a secret `GEMINI_API_KEY` prompt without a value, and `/api/v1/health` as the health check. `ALLOWED_ORIGINS` supplies comma-separated CORS origins, defaulting to `http://localhost:3000`. `create_app` already seeds an empty SQLite store at startup. No deploy was performed.

Final verification: `DEMO_MODE=1 .venv/bin/python scripts/dump_api_examples.py` regenerated 30 valid JSON response examples (29 HTTP 2xx, final deliberate HTTP 404). `ruby` parsed `backend/render.yaml` and checked its required fields. `.venv/bin/python -m ruff check app tests eval scripts`: **All checks passed!** `.venv/bin/python -m pytest -q`: **67 passed, 1 skipped, 1 warning in 24.10s**. The skip is the opt-in live Gemini test, which passed separately as recorded above. No commit, push, or deploy was performed.
