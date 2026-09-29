# CONTRACT — the shared rules between backend and frontend
Owner: Claude (instructor). Only Claude edits this file. Backend and frontend both build against it.
Version: 0.7 (29 Sep 2026) — see "v0.7" at the end. **docs/api-examples.md holds REAL responses for every endpoint: it is the source of truth for JSON shapes.**

## Product
Refill-resolution loop for diabetes / hypertension patients at government health centres (PHCs):
patient or ASHA reports a failed refill → pharmacist verifies → district sees need vs stock + warnings → AI drafts a stock transfer → officer approves → dispatched → received → patient supplied → case closed.
All demo data is synthetic and must be labelled "Synthetic demo data".

## Roles
`patient`, `asha`, `pharmacist`, `district_officer`. Demo login = pick a seeded user (no passwords in demo; header `X-Demo-User: <user_id>`). Each role sees only its own endpoints (403 otherwise).

## Entities (JSON, snake_case, ISO-8601 UTC timestamps)
- **Facility** `{id, name, type: "PHC"|"CHC"|"district_store", block, district, lat, lng}`
- **Drug** `{id, name, form: "tablet"|"capsule"|"injection", strength: "500 mg", unit: "tablet"}`  — units always counted in `unit`.
- **User** `{id, role, name, facility_id, language: "hi"|"en", phone_masked}`
- **Patient** `{id, name, age, sex, conditions: ["T2D"|"HTN"], facility_id, asha_id, language}`
- **Prescription** `{id, patient_id, drug_id, dose_per_day, days_supply, start_date, confirmed_by_staff: bool, active: bool}`
- **Batch** `{id, facility_id, drug_id, quantity, expiry_date}`
- **StockSnapshot** `{facility_id, drug_id, on_hand, batches:[Batch], recorded_at, recorded_by, source: "manual"|"dvdms_import"}`  — every stock number carries `recorded_at`; clients show its age.
- **DispensingRecord** `{facility_id, drug_id, patient_id|null, quantity, dispensed_at}`
- **Case** `{id, patient_id, facility_id, drug_id, requested_qty, received_qty, household_supply_days, attempted_at, reported_by, channel: "voice"|"manual", transcript|null, status, verification: {result: "confirmed_stockout"|"stock_available"|"household_only"|null, on_hand|null, by|null, at|null}, transfer_id|null, created_at, updated_at}`
- **CaseEvent** `{id, case_id, from_status, to_status, actor_id, at, note}` — append-only audit trail.
- **Transfer** `{id, drug_id, from_facility_id, to_facility_id, quantity, batch_ids, status: "draft"|"approved"|"rejected"|"dispatched"|"received", drafted_by: "agent"|user_id, rationale, constraints_checked: {donor_safety_stock_ok, expiry_ok, units_ok}, approved_by|null, created_at}`

## Case status machine
`reported → verified → (transfer_drafted → transfer_approved → dispatched → received) → supplied → closed`
Side exits: `verified` with result `stock_available` → `supplied` directly; `household_only` → `closed` (note: not a facility stock-out); any state → `cancelled` (with note). A transfer draft may end `no_feasible_transfer` (case stays `verified`, escalated flag true).
Every transition writes a CaseEvent. Illegal transitions → 409.

## Forecast rules (district)
- `cohort_need(facility, drug, horizon_days)` = sum over active, staff-confirmed prescriptions of dose_per_day × days in horizon.
- `dispensing_forecast` = Croston/TSB on daily dispensing; days during recorded stock-outs are flagged as censored (not treated as true zero demand).
- Shown SEPARATELY. Combined estimate = `max(cohort_need, dispensing_forecast)` for enrolled-dominant drugs (documented rule; no summing → no double counting).
- `days_left = on_hand / max(daily combined estimate, ε)`; warning levels: `critical` < 7 days, `low` < 14 days.

## Transfer engine rules
Donor keeps safety stock = 14 days of its own combined estimate. Only batches expiring > 30 days after arrival. Same drug_id + unit only. Min-cost flow (OR-Tools) on distance. If nothing feasible → `no_feasible_transfer` with reason.

## API (prefix `/api/v1`)
| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | /health | any | liveness |
| GET | /me | any | current demo user |
| GET | /demo/users | any | list seeded users to pick |
| GET | /facilities, /drugs | any | reference data |
| GET | /patients/{id} | patient(self), asha, pharmacist | patient + prescriptions |
| POST | /cases | patient, asha | create case (manual fields) → status `reported` |
| POST | /cases/voice | patient, asha | multipart audio (+ lang) → extracted fields + transcript, NOT saved until confirmed |
| POST | /cases/voice/confirm | patient, asha | save confirmed fields as a case |
| GET | /cases?status=&facility_id= | role-scoped | list |
| GET | /cases/{id} | role-scoped | case + events + transfer |
| GET | /notifications | patient, asha | medicine delivery and supply notices |
| POST | /notifications/{id}/read | patient, asha | mark one visible notice read |
| POST | /cases/{id}/verify | pharmacist | body `{result, on_hand}` |
| POST | /cases/{id}/supply | pharmacist | mark supplied `{quantity}` |
| POST | /cases/{id}/confirm-received-by-patient | patient, asha | → closed |
| POST | /stock | pharmacist | new StockSnapshot |
| GET | /district/overview?district= | district_officer | per facility × drug: on_hand, recorded_at, cohort_need, dispensing_forecast, combined, days_left, warning, open_cases |
| POST | /transfers/draft | district_officer | `{case_id}` → agent drafts via engine (+ Gemini rationale) |
| POST | /transfers/{id}/approve, /reject | district_officer | |
| POST | /transfers/{id}/dispatch | district_officer | |
| POST | /transfers/{id}/receive | pharmacist (receiving) | |
| POST | /sync/batch | any | offline queue: list of idempotent ops with client `op_id`; duplicates ignored |

Errors: `{error: {code, message}}`. Idempotency: POSTs accept header `Idempotency-Key`.

## Safety rules (enforced in backend)
No blood-sugar numbers anywhere. No medical advice text generated for patients. Gemini output is only: extracted fields, transcript, transfer rationale. Every agent action is a draft until a human approves.

## v0.2 decisions (answers to Codex questions)
1. **One donor per transfer.** The engine picks the cheapest single donor that can cover the full request alone. If none can, result = `no_feasible_transfer` with reason `needs_split_or_supply` (case stays `verified`, `escalated: true`). Splitting across donors is roadmap.
2. **Transfer rejected** → transfer `rejected`; case returns from `transfer_drafted` to `verified` (officer may request a new draft). New transfer status `cancelled`: if a case is cancelled before dispatch, its approved/draft transfer becomes `cancelled`. If already dispatched, the transfer continues to `received` (stock still arrives) and the case is `cancelled` with a note.
3. **Add** `POST /cases/{id}/cancel` `{note}` (patient, asha, pharmacist, district_officer within scope). Terminal cases (`closed`, `cancelled`) cannot be cancelled.
4. **Offline ops shape:** `{op_id, method: "POST", path, body}`; ops are independent; each returns `{op_id, status: "applied"|"duplicate"|"error", result|error}`; one failure does not stop later ops.
5. **Horizon** default 30 days, query param `horizon_days` (7–90). All demo drugs use the enrolled-dominant `max` rule; per-drug rule field `demand_rule: "max"|"dispensing_only"` on Drug, default `max`.
6. **Visibility:** accept your assumptions (patient = self; ASHA = assigned patients; pharmacist = own facility; district officer = own district). Demo user picker is public (demo only; flagged in README as not for production).
7. **Partial supply:** new status `partially_supplied`. `POST /cases/{id}/supply {quantity}` adds to `received_qty`; when `received_qty >= requested_qty` → `supplied`. Allowed from `verified` (stock_available), `received`, or `partially_supplied`.
8. **`received_qty`** = units handed to the patient (not units received at the facility). Facility receipt lives on the Transfer.

## v0.3 additions
- `POST /api/v1/demo/reset` (any demo user; disabled when env `DEMO_MODE` is not "1") → re-seeds the deterministic synthetic data and returns `{ok, seeded_at}`. Used before recording the demo video.
- `GET /api/v1/demo/scenario/ramesh` (any) → ids needed to play the Ramesh story: `{patient_id, asha_id, pharmacist_id, district_officer_id, facility_id, donor_facility_id, drug_id}`. Seed guarantees: Ramesh's PHC is out of metformin 500 mg; exactly one nearby PHC has a feasible donation.
- `GET /api/v1/evaluation/summary` (district_officer) → latest offline evaluation results (JSON written by the eval scripts), so the UI/deck can show them.

## v0.4 (29 Sep 2026)
1. **Exact shapes = docs/api-examples.md** (generated from the running backend by `backend/scripts/dump_api_examples.py`; Codex regenerates it after any API change). If this file and the prose above disagree, the examples win; tell Claude.
2. **`POST /sync/batch` body is an object:** `{"ops": [{op_id, method, path, body}, ...]}` — never a bare list. `path` is relative to `/api/v1`.
3. **`GET /district/overview` returns a flat list**, one row per facility × drug: `[{facility_id, drug_id, on_hand, recorded_at, cohort_need, dispensing_forecast, calibrated_cohort_need, unenrolled_dispensing_forecast, demand_rule, combined, horizon_days, days_left, warning, open_cases, ...}]`. The frontend groups it itself.
4. **Voice flow:** `POST /cases/voice` multipart (`audio` file, `lang` = "hi"|"en") → `{fields:{patient_id, drug_id, requested_qty, household_supply_days, attempted_at}, transcript, ai_source, synthetic_label}` — nothing saved. The user edits the fields, then `POST /cases/voice/confirm {fields, transcript}` → Case.
5. **`ai_source`** on every AI-touched response: `"gemini"` | `"fake"` | `"fallback"`. The UI shows a badge when it is not `"gemini"`: "Drafted by rules — AI unavailable".
6. **Forecast default stays `DEMAND_RULE=max`.** The calibrated rule (B14) was REJECTED as default: it lowers error but loses the unmet-patient-days benefit (baseline 227.58 vs 3.33). It stays available behind the setting and is reported honestly on the evaluation page.

## v0.5 (29 Sep 2026) — endpoints the designed screens need
1. `GET /patients` (role-scoped: patient = self, asha = assigned, pharmacist = own facility, district_officer = own district) → `[Patient + {prescriptions:[Prescription], open_case: Case|null}]`.
2. `GET /transfers?status=&facility_id=` (district_officer = own district; pharmacist = transfers to OR from own facility) → `[Transfer]` newest first. `GET /transfers/{id}` → Transfer. Transfer JSON always includes `case_id`, `batch_allocations:[{batch_id, quantity, expiry_date}]`, `ai_source`, and `ai_model` when Gemini answered.
3. `GET /district/series?facility_id=&drug_id=&days=60` (district_officer) → `{facility_id, drug_id, days:[{date, on_hand, dispensed, stockout}], cohort_need_daily, dispensing_forecast_daily, combined_daily, days_left, horizon_days}`.
4. Display names: every Facility, Drug, User and Patient carries `name` (English) and `name_hi` (Devanagari). Demo cast: patient-001 = Ramesh, 54 (रमेश); asha-1 = Rekha (रेखा); pharmacist-1 = Sunita (सुनीता); officer-1 = Dr. Mehra (डॉ. मेहरा). Other patients get ordinary Indian names. `synthetic_label` stays on everything.
5. `GET /stock?facility_id=` (pharmacist = own facility; district_officer = own district) → latest StockSnapshot per drug: `[{facility_id, drug_id, on_hand, batches, recorded_at, recorded_by, source}]`.

## v0.6 (29 Sep 2026) — voice extraction must not invent
1. `POST /cases/voice` → `fields` values are `null` when the speaker did not say them (drug_id, requested_qty, household_supply_days, attempted_at). Never default. `patient_id` stays filled from the logged-in patient / chosen patient. Add `missing: [field names]`.
2. `transcript` is in Devanagari when the speech is Hindi (English words may stay in Latin).
3. If the speech is not a refill problem at all, return all fields null and `not_a_refill_report: true`.

## v0.7 (29 Sep 2026) — medicine notifications

- `GET /api/v1/notifications` uses the same `X-Demo-User` authentication as `/cases`. Patients see notices for their own cases; ASHAs see notices for cases of the patients they cover. Every other role receives `[]`. Results are newest first.
- Each notice has exactly `{id, case_id, kind, drug_id, facility_id, at, read, hi, en}`. `id` is the case event ID; `at` is its ISO-8601 UTC time. `kind` maps `dispatched` → `on_the_way`, `received` → `arrived`, and `supplied` or `partially_supplied` → `given`. No other case events make notices. `hi` and `en` use the seeded drug and facility names. No invented quantities or medical advice.
- `POST /api/v1/notifications/{id}/read` returns `{id, read: true}`. It returns 404 for an unknown notice or one the caller cannot see. Read state is stored separately per demo user in the database, and `/demo/reset` deletes it.
