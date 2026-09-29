# Saathi submission deck — 11 slides

Use the linked screenshots from `frontend/e2e/shots/`; crop to the relevant panel and keep the **Synthetic demo data** label visible. All slide figures below come from the linked evaluation report or implementation notes. The roadmap bullets are proposals from `~/dev/c4c2-ideas/PLAN.md` (§0.4 and §0.6), not current capabilities.

## 1. Saathi · साथी: close the refill loop

- A patient or ASHA reports a refill that the PHC did not supply. [Contract](CONTRACT.md#product)
- The case stays visible through pharmacist check, transfer, handover, and patient confirmation. [Contract](CONTRACT.md#case-status-machine)
- This is a synthetic prototype for a Track 3 supply-chain workflow. [Notes](notes-codex.md#b10b13-continuation-28-sep-2026)

Screenshot: [landing](../frontend/e2e/shots/L1-landing.png).

## 2. One case: Ramesh's metformin

- Ramesh's seeded Sundarpur PHC starts with no metformin. [Seed notes](notes-codex.md#round-8-seed-realism-follow-up-29-sep-2026)
- The patient flow saves a **reported** case; it does not call the shelf empty until staff verify. [Browser story](../frontend/e2e/ramesh.spec.ts)
- The same case ID follows the whole browser story, ending at `closed`. [Browser story](../frontend/e2e/ramesh.spec.ts)

Screenshot: [reported case](../frontend/e2e/shots/04-patient-case-reported.png).

## 3. Hindi report with a human read-back

- An ASHA selects Ramesh and records a Hindi refill report. [ASHA browser story](../frontend/e2e/voice-asha.spec.ts)
- The voice route returns a transcript and editable medicine, date, quantity, and home-supply fields. [Contract](CONTRACT.md#v04-29-sep-2026)
- Missing fields block sending until a person fills them; extraction alone creates no case. [Contract](CONTRACT.md#v06-29-sep-2026)
- The browser test uses a labeled synthetic TTS clip through Chromium's fake microphone. [ASHA browser story](../frontend/e2e/voice-asha.spec.ts)

Screenshot: [ASHA check screen](../frontend/e2e/shots/v3-asha-check.png).

## 4. Verify the shortage at the shelf

- A pharmacist sees the report in the verification queue. [Browser story](../frontend/e2e/ramesh.spec.ts)
- Sunita records the on-hand count and confirms the stockout before the district acts. [Browser story](../frontend/e2e/ramesh.spec.ts)
- Stock snapshots carry a timestamp; the district screen shows data age. [Contract](CONTRACT.md#entities-json-snake_case-iso-8601-utc-timestamps)

Screenshot: [pharmacist verification](../frontend/e2e/shots/05-pharmacist-verify.png).

## 5. District visibility: need beside stock

- The overview shows stock, its age, prescription need, dispensing forecast, days left, warnings, and open cases by centre and medicine. [District UI](../frontend/src/app/district/page.tsx)
- Prescription need and dispensing forecast are separate; the default planning estimate takes the larger, not their sum. [Contract](CONTRACT.md#forecast-rules-district)
- Known stockout dates are excluded from the dispensing series so an empty shelf does not become a zero-demand day. [Forecast implementation](../backend/app/domain/forecast.py)

Screenshot: [district overview](../frontend/e2e/shots/06-officer-overview.png).

## 6. Forecast: a useful signal with real trade-offs

- The evaluation is an independent **synthetic simulation**, not a field outcome. [Forecast report](../backend/eval/results/forecast.md)
- Baseline **experimental combined** error was **3.81 units/day**, versus **4.98** for dispensing-only; the shipped default is the separate `max` rule. [Forecast report](../backend/eval/results/forecast.md) [Contract](CONTRACT.md#v04-29-sep-2026)
- Both had **227.58 unmet patient-days**; prescription-only had **3.33** with **389.19 overstock units**. [Forecast report](../backend/eval/results/forecast.md)
- With stale prescriptions, combined error rose to **17.51 units/day** and mean overstock to **236.45 units**. [Forecast report](../backend/eval/results/forecast.md)

Screenshot: [district overview context](../frontend/e2e/shots/06-officer-overview.png). Put the four figures in a separate, clearly labeled **Synthetic simulation** chart; the screenshot itself shows demo stock, not these evaluation results.

## 7. Draft a constrained transfer; officer decides

- OR-Tools seeks one feasible donor by distance after unit, expiry, and donor safety-stock checks. [Transfer rules](CONTRACT.md#transfer-engine-rules)
- In Ramesh's synthetic scenario, Nayagaon PHC is the feasible metformin donor. [Seed notes](notes-codex.md#round-8-seed-realism-follow-up-29-sep-2026)
- Gemini may explain checked engine facts; it does not select an unsafe donor or approve the move. [AI notes](notes-codex.md#b16b19-continuation-29-sep-2026)
- If no donor qualifies, the API returns `no_feasible_transfer`. [Transfer API](../backend/app/api/transfers.py)

Screenshot: [officer transfer draft](../frontend/e2e/shots/07-officer-transfer-draft.png).

## 8. Follow through to medicine in hand

- The officer approves and marks the transfer dispatched. [Browser story](../frontend/e2e/ramesh.spec.ts)
- The pharmacist records receipt, then hands medicine to Ramesh. [Browser story](../frontend/e2e/ramesh.spec.ts)
- Ramesh confirms receipt to close the case; the audit drawer shows the event sequence. [Browser story](../frontend/e2e/ramesh.spec.ts)

Screenshot: [patient closed](../frontend/e2e/shots/12-patient-closed.png). Optional inset: [audit drawer](../frontend/e2e/shots/13-officer-audit.png).

## 9. Voice evidence, and its narrow limits

- In a paced API test, **12/12 synthetic Hindi TTS clips** got live Gemini answers and matched scripted medicine, quantity, home days, and date fields. [Audio report](../backend/eval/results/audio.md)
- Mean API latency was **5.96 seconds**; the transcript proxy was not word error rate. [Audio report](../backend/eval/results/audio.md)
- One real WhatsApp clip was **not a refill report** and was correctly classified on a standalone retry; an earlier call fell back with no classification evidence. [Audio report](../backend/eval/results/audio.md)
- Real refill speech, dialects, and noisy settings are barely tested. [Audio report](../backend/eval/results/audio.md)

Screenshot: [ASHA voice review](../frontend/e2e/shots/v3-asha-check.png). Caption the screenshot **synthetic TTS browser demo**; the real WhatsApp clip is only an API evaluation.

## 10. Safety and pilot gate

- Voice fields need human confirmation; the app must not invent missing details or give treatment advice. [Contract](CONTRACT.md#v06-29-sep-2026)
- A pharmacist verifies stock and an officer approves a constrained transfer. [Contract](CONTRACT.md#product)
- Demo login and SQLite are synthetic-demo choices, not field-grade identity or persistence. [Backend setup](../backend/README.md#demo-and-deployment-configuration)
- Proposed pilot: name the stock custodian and transfer authority, define response deadlines, and measure stockout days and patients without medicine using real data. [Project plan: §0.4, §0.6](../../c4c2-ideas/PLAN.md)

Screenshot: [login and reset](../frontend/e2e/shots/01-login-reset.png).

## 11. Next: validate, then extend

- Near term: test consented real Hindi refill speech and usability with ASHAs and pharmacists. [Project plan: §0.6](../../c4c2-ideas/PLAN.md)
- Pilot-ready work: stock-register or authoritative stock imports, consent and privacy, and a real transfer workflow. [Project plan: §0.6](../../c4c2-ideas/PLAN.md)
- Doctor summaries, WhatsApp/IVR, health-system integration, meal/glucose models, federated learning, and quantum comparisons are **roadmap or research**, not shipped features. [Project plan: §0.4, §0.6](../../c4c2-ideas/PLAN.md)
- The immediate ask is a supervised field test that can measure whether cases close faster and patients actually receive medicine. [Project plan: §0.6](../../c4c2-ideas/PLAN.md)

Screenshot: [closed case](../frontend/e2e/shots/12-patient-closed.png).
