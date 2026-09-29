# Codex round 16 — backend for fixes A, C, D, E (29 Sep 2026)

You are the backend builder for Saathi (repo root = this folder). Read docs/HANDOFF.md (top), docs/CONTRACT.md, docs/notes-codex.md first.
**Do NOT edit anything under frontend/** — Antigravity is working there at the same time. Do not commit, push or deploy.
Write your report to docs/out-codex-16.md and append a dated section to docs/notes-codex.md.

## A1 — Keep the live server awake
- `GET /api/v1/health` must stay instant: no database, no AI call. Add a test that it answers in < 50 ms under TestClient.
- Add `.github/workflows/keep-awake.yml`: `schedule: cron "*/10 * * * *"` plus `workflow_dispatch`; one step: `curl -fsS --max-time 90 https://saathi-api-gm4i.onrender.com/api/v1/health` with 3 retries. No secrets.
- In out-codex-16.md state plainly: GitHub may delay scheduled runs, and on a PRIVATE repo this uses ~4,300 Action-minutes/month (over the 2,000 free) — it is only free once the repo is public. Do not change repo visibility.

## C1 — "Medicine arrived" notifications (contract v0.7 — implement EXACTLY this shape; the frontend is being built against it in parallel)
- `GET /api/v1/notifications` — same demo auth as `/cases`. Role `patient`: own cases. Role `asha`: cases of the patients she covers. Any other role: `[]`.
  Returns newest first:
  ```json
  [{"id": "<case event id>", "case_id": "case-…", "kind": "on_the_way" | "arrived" | "given",
    "drug_id": "metformin", "facility_id": "phc-1", "at": "ISO-8601 UTC", "read": false,
    "hi": "आपकी मेटफॉर्मिन सुंदरपुर PHC पहुँच गई है। आज ले लें।", "en": "Your Metformin has reached Sundarpur PHC. Collect it today."}]
  ```
  Mapping from case events: `dispatched`→`on_the_way`, `received`→`arrived`, `supplied` or `partially_supplied`→`given`. No other events produce notifications. Use real drug and facility names from the seed in both languages; no invented numbers or medical advice.
- `POST /api/v1/notifications/{id}/read` → `{"id": "…", "read": true}`; 404 for an unknown id or one the caller cannot see. Read-state must persist in the database and must be wiped by `/demo/reset`.
- Update docs/CONTRACT.md to v0.7 with this section and add examples to docs/api-examples.md.
- Tests: the full Ramesh flow produces exactly on_the_way → arrived → given for Ramesh; another patient sees none of Ramesh's; mark-read persists; reset clears it.

## D1 — Real-voice testing harness (the recordings come from Aditya)
- Only one real clip exists (r01, not a refill report). You cannot record humans — do not generate TTS and call it real.
- Make `eval/audio_eval.py` also run every clip in `backend/eval/audio/real/` that has a matching `<name>.json` label (same label format as the synthetic ones; `r01.json` is the example). Unlabelled clips are skipped and listed.
- Write `backend/eval/audio/real/RECORDING-GUIDE.md` for Aditya in plain words: record 6 WhatsApp voice notes (2–3 different people if possible), each one telling a refill problem naturally in Hindi — no script. Give 6 one-line situations (e.g. "your BP tablet ran out, you went to the PHC yesterday, they said come next week"), what to write in each .json label afterwards, and the one command to run the eval. Keep it to one page.

## E1 — Offline sync, backend side
- Add/confirm tests for `POST /api/v1/sync/batch` with a queued `POST /cases` op exactly as the frontend sends it (see frontend/src/app/patient/report/page.tsx line ~120 and frontend/src/lib/OfflineQueueContext.tsx — read only): sending the same `op_id` twice creates ONE case; an op whose body is missing a required field returns a per-op error and does not block the other ops in the batch.

## Done means
`cd backend && .venv/bin/pytest -q` all pass (report the count; it was 100 before), `ruff check` clean, the Ramesh script `scripts/play_ramesh.py` still completes. List every file you changed. Say honestly anything not done.
