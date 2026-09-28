# Saathi · साथी — submission README draft

Saathi helps patients and ASHA workers report a medicine refill they could not get at a primary health centre. It carries that report through staff verification, a proposed stock transfer, and patient confirmation that the medicine was supplied.

This is a **synthetic demo**, built for the refill-resolution loop described in [`CONTRACT.md`](CONTRACT.md) and [`HANDOFF.md`](HANDOFF.md). It is not a clinical decision tool or a production login system.

## Follow Ramesh's case

Ramesh's seeded centre, Sundarpur PHC, has no metformin. Ramesh or his ASHA reports the failed refill, using Hindi voice or a manual form; the voice route returns a transcript and editable fields before any case is saved. A pharmacist checks the stock and confirms the shortage. The district view shows stock, prescription-based need, dispensing-based forecast, and stock age. The transfer engine finds eligible stock at Nayagaon PHC, drafts a transfer, and asks a district officer to approve it. Staff dispatch and receive the stock, supply Ramesh, and Ramesh confirms receipt. Every change appears in the case event history. See [`play_ramesh.py`](../backend/scripts/play_ramesh.py), [`data.py`](../backend/app/seed/data.py), and [`CONTRACT.md`](CONTRACT.md).

## Run locally

Use Python 3.11 or newer and Node.js [VERIFY: minimum Node version]. From the repository root:

```sh
python3.11 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e 'backend[dev]'
cd backend
DEMO_MODE=1 .venv/bin/uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. The frontend defaults to the backend at `http://localhost:8000`; set `NEXT_PUBLIC_API_BASE` if it runs elsewhere. For live Gemini drafts, put `GEMINI_API_KEY` in `backend/.env`. Without a key, the backend uses a deterministic demo response; provider failure is marked `ai_source: "fallback"`. These settings come from [`backend/README.md`](../backend/README.md), [`main.py`](../backend/app/main.py), and [`api.ts`](../frontend/src/lib/api.ts). [VERIFY: complete browser walk-through after the concurrent frontend fixes land.]

The demo role picker uses seeded users, without passwords. Use `patient-user-001` for Ramesh, `asha-1`, `pharmacist-1`, and `officer-1` for the main story. `GET /api/v1/demo/users` lists the full synthetic roster. `POST /api/v1/demo/reset` restores local seed data when `DEMO_MODE=1`; it deletes the current local records, so use it only on the demo database. See [`data.py`](../backend/app/seed/data.py) and [`demo.py`](../backend/app/api/demo.py).

## How it works

- **API and records:** FastAPI serves role-scoped routes, a case state machine, append-only events, and SQLite demo storage. [`app/`](../backend/app/) contains the implementation.
- **Demand view:** staff-confirmed prescriptions and a TSB dispensing forecast appear separately; recorded stockout days are omitted from the dispensing series. The default combined estimate is the larger of the two. [`forecast.py`](../backend/app/domain/forecast.py) and [`CONTRACT.md`](CONTRACT.md) define the rules.
- **Transfer draft:** OR-Tools selects one eligible donor using distance after checks for medicine units, donor safety stock, and batch expiry. A human officer approves the draft; dispatch checks stock again. [`transfers.py`](../backend/app/domain/transfers.py) implements this.
- **Gemini and fallback:** the voice endpoint sends the uploaded audio bytes as an inline Gemini audio part and validates the transcript and fields. Gemini may draft a transfer rationale from engine-checked facts. A provider outage uses a marked deterministic fallback; unsafe output needs manual review. [`ai.py`](../backend/app/domain/ai.py) and [`voice.py`](../backend/app/api/voice.py) implement this.
- **Web and offline:** the Next.js frontend contains an IndexedDB queue; the backend accepts idempotent batches at `/api/v1/sync/batch`. See [`OfflineQueueContext.tsx`](../frontend/src/lib/OfflineQueueContext.tsx) and [`sync.py`](../backend/app/api/sync.py). [VERIFY: browser replay and end-to-end reconnect behavior after frontend integration.]

## Safety and limits

The app records a **reported** shortage until a pharmacist verifies stock. A voice draft is shown for correction before saving. Model output is checked for the required fields and screened for medical advice or blood-sugar numbers; it does not prescribe treatment. An officer approves transfer drafts, and the backend checks stock, units, expiry, and donor safety stock. These are demo safeguards, not a substitute for clinical or inventory governance. Demo authentication uses a selectable user ID and must be replaced before real deployment. See [`CONTRACT.md`](CONTRACT.md), [`ai.py`](../backend/app/domain/ai.py), and [`transfers.py`](../backend/app/api/transfers.py).

## Honest evaluation

The forecast experiment uses independently generated patient need and twelve seeded repetitions per scenario. A simulated order arrives after seven days and is sized to 130% of forecast. These are simulator outcomes, not field effectiveness estimates. In the baseline, the default combined method had mean absolute error of **3.81 units/day**, compared with **4.98** for dispensing alone. Its **227.58 unmet patient-days** were much higher than prescription-only's **3.33**; prescription-only also carried **389.19 mean overstock units** versus combined's **0.02**. With stale prescriptions, combined had **17.51 MAE/day** and **236.45 overstock units**, versus dispensing-only's **3.57** and **0.97**. The lower forecast error does not erase the cost of over-forecasting or missed supply. Full methods and rows: [`forecast.md`](../backend/eval/results/forecast.md) and [`forecast.json`](../backend/eval/results/forecast.json).

The earlier text-only Hindi/Hinglish corpus had **26 live Gemini answers out of 30**, with **4 provider failures**. Across all 30 samples, medicine accuracy was **0.867**, requested quantity **0.833**, household supply days **0.867**, and negation in the returned transcript **0.967**. It did not test speech recognition; facility and received quantity are absent from the product schema. See [`extraction.json`](../backend/eval/results/extraction.json).

We then posted **12 synthetic Hindi TTS clips** through the actual voice route. All twelve API calls returned, but only **9/12** received a live Gemini answer; three used the marked fallback. All nine live answers used `gemini-3.1-flash-lite`. Among them, medicine, requested quantity, and household days each matched **9/9** gold labels; attempted date matched **8/9**. Mean live-answer latency was **9.46 seconds**, and the mean across all calls, including provider failures, was **14.85 seconds**. The two “medicine was received” clips each succeeded on a separate paced retry, while one Hinglish clip still fell back. These figures and every wrong field are in [`audio.md`](../backend/eval/results/audio.md) and [`audio.json`](../backend/eval/results/audio.json).

Every seeded patient, facility, stock record, evaluation scenario, and TTS voice clip is labeled **Synthetic demo data**. TTS audio is cleaner and easier than spontaneous rural speech. The real-audio folder is empty until recordings are supplied; real-speech accuracy is [VERIFY].

## Roadmap

Test with consented real Hindi speech and field users; measure comprehension, correction rate, missed shortages, and time to confirmed supply. Integrate with an authoritative medicine stock system, strengthen identity and access controls, support split transfers, and validate the forecast with observed demand before district use. Doctor-linked prescriptions and other health features from [`HANDOFF.md`](HANDOFF.md) remain ideas for later evaluation, not functions shown by this demo.
