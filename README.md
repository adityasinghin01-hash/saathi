# Saathi · साथी

Saathi is a Hindi-first, **synthetic demo** of a medicine refill-resolution loop for primary health centres. A patient or ASHA reports a failed refill; a pharmacist checks stock; a district officer reviews a proposed transfer; and the case stays open until the patient confirms receiving the medicine. It is a prototype, not clinical software or a production inventory system.

## Run locally

Use Python 3.11 and a Node.js installation compatible with the pinned Next.js release. From the repository root, start the API:

```sh
python3.11 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e 'backend[dev]'
cd backend
DEMO_MODE=1 .venv/bin/uvicorn app.main:app --port 8000
```

In another terminal, start the web app:

```sh
cd frontend
npm ci
NEXT_PUBLIC_DEMO_MODE=1 npm run dev
```

Open `http://localhost:3000`. The frontend uses `http://localhost:8000` by default; set `NEXT_PUBLIC_API_BASE` to another backend origin when needed. The backend reads `GEMINI_API_KEY` from its environment or ignored `backend/.env`; without a key it uses a labeled deterministic fake. Never put the key in `NEXT_PUBLIC_` variables. See [frontend setup](frontend/README.md), [backend setup](backend/README.md), and [deployment steps](docs/DEPLOY.md).

On `/login`, choose a synthetic role: **Ramesh** (`patient-user-001`), **Rekha** (`asha-1`), **Sunita** (`pharmacist-1`), or **Dr. Mehra** (`officer-1`). The **Reset demo** button restores the seed and deletes current demo cases, so use it only with demo data. Demo login is a role picker without passwords. The [Ramesh browser story](frontend/e2e/ramesh.spec.ts) and [ASHA voice story](frontend/e2e/voice-asha.spec.ts) show the exact screen flow.

## What the prototype does

1. Ramesh or Rekha reports a missed metformin refill by form or Hindi voice. Voice returns a transcript and editable fields; it does **not** save a case until the user confirms.
2. Sunita verifies the reported shortage against timestamped stock. Until that check, the shortage remains a **report**, not a confirmed stockout.
3. The district screen shows enrolled patients' prescription need, a separate dispensing forecast, stock age, days left, and warnings. The default planning estimate takes the larger forecast instead of summing them. Recorded stockout days are excluded from the dispensing series.
4. OR-Tools proposes an eligible stock transfer after unit, expiry, and donor reserve checks; Gemini may word a rationale using checked facts. An officer approves; staff dispatch, receive, and hand over medicine; Ramesh confirms receipt. Each status change is in the case history.

The [FastAPI backend](backend/app/) stores the synthetic scenario in SQLite. The [Next.js frontend](frontend/src/) supplies patient, ASHA, pharmacist, and district views. Its IndexedDB queue can hold supported offline writes for later `/api/v1/sync/batch` replay. See the [shared contract](docs/CONTRACT.md), [API examples](docs/api-examples.md), and [implementation notes](docs/notes-codex.md).

## Safety and data limits

- All seeded patients, facilities, stock records, and forecast scenarios are **Synthetic demo data**. The Hindi TTS clips are synthetic too. One separately evaluated WhatsApp audio clip is a real human voice, used only for the stated voice test; it is not a patient record in the app.
- The voice review screen marks missing fields and requires a human to complete them before case creation. A non-refill statement must not be turned into a refill case. Model text is screened for medication advice and invented blood-sugar numbers; the filter is limited and is not a clinical safety classifier.
- Transfer drafts need an officer's approval. Dispatch checks stock again. If no donor can satisfy the constraints, the engine reports no feasible transfer instead of inventing one.
- Demo role selection is not secure identity verification. SQLite demo storage, browser offline sync, and simulated forecasts need field validation and operational controls before real use.

## Honest evaluation

The [forecast experiment](backend/eval/results/forecast.md) generates patient need independently of the tested methods, then simulates incomplete enrollment, stock-limited dispensing, and other stressors. These are **simulator outcomes**, not measured health impact. In the baseline, the **experimental combined method** had mean absolute error of **3.81 units/day**, versus **4.98** for dispensing-only. Both had **227.58 unmet patient-days**; prescription-only had **3.33**, but **389.19 mean overstock units** versus combined's **0.02**. Under stale prescriptions, experimental combined error rose to **17.51 units/day** and overstock to **236.45 units**, versus dispensing-only's **3.57** and **0.97**. The shipped product still defaults to the separate `max` rule; the experimental combined method is not its default. Lower error in one scenario does not establish fewer missed refills.

The [text-only Hindi/Hinglish test](docs/notes-codex.md#b16b19-continuation-29-sep-2026) received **26 live answers out of 30** synthetic transcripts; **4** calls failed. Across all **30**, medicine accuracy was **0.867**, requested quantity **0.833**, household supply days **0.867**, and negation in the transcript **0.967**. This test did **not** test speech recognition. Facility and received quantity are outside the product extraction schema, so their zero scores are not model accuracy scores.

The latest [audio evaluation](backend/eval/results/audio.md) sent **12 synthetic Hindi TTS clips** through the voice API. All **12/12** received live Gemini responses; medicine, requested quantity, household days, and spoken date each matched the scripted labels in **12/12** clips. Mean API latency was **5.96 seconds**. The transcript check was limited to script facts and Devanagari presence, not word error rate. A **single real WhatsApp Ogg/Opus clip** was a general health complaint, **not a refill report**. Its standalone live retry classified it as `not_a_refill_report: true` with all audio-extracted fields null; an earlier paced call fell back and provided no classification evidence. **Real speech is barely tested**: this one negative clip says nothing about accuracy on real refill requests, dialects, noisy clinics, or varied phones.

## Roadmap

The project plan (`~/dev/c4c2-ideas/PLAN.md`, sections 0.4 and 0.6) separates the current refill prototype from future work. Near-term work is real user and consented speech testing, a pilot protocol with named stock and transfer owners, stronger identity and privacy controls, and an authoritative stock import. Later ideas include ASHA task support, doctor summaries, WhatsApp/IVR, stock-register photo reading, and health-system integrations. Meal and glucose models, federated learning, and a quantum experiment are research proposals, **not shipped Saathi features**. A field pilot would measure actual stockout days, patients without medicine, private spending, and alert lead time before any effectiveness claim.
