# Antigravity F3 — frontend for fixes A, B, C, E (29 Sep 2026)

You are working on the Saathi frontend in `~/dev/refill-loop/frontend` (Next.js). Read first: `frontend/AGENTS.md`, `docs/CONTRACT.md`, `docs/HANDOFF.md` (top section), and look at the existing components in `src/components/` (ui.tsx, shells.tsx) — reuse them, and keep the Saathi look (terracotta clay, the `Bi` bilingual label, `.sa-*` classes). Every piece of text you add must be bilingual (Hindi + English) through the existing pattern — no hard-coded English strings.

**Hard rules**
- Do NOT edit anything in `backend/`. Codex is working there at the same time.
- Do NOT change, skip, loosen or delete any existing test or assertion (`e2e/ramesh.spec.ts`, `e2e/voice-asha.spec.ts`, `__tests__/`). A test that passes because it was weakened counts as a failure. If an existing test breaks, fix the app, not the test.
- Do not commit, push or deploy.

## A2 — "Waking up" screen
The live backend (Render free plan) sleeps after 15 min idle and takes up to ~60 s to wake. Right now a visitor sees a broken-looking page.
- On app start, call `GET {API_BASE}/api/v1/health`. If it hasn't answered within 1.5 s, show a full-screen friendly wake screen: Saathi mark, "सर्वर जाग रहा है… / Waking up the server…", a line saying it can take up to a minute on the free server, and a progress indicator. Retry every 3 s until it answers, then fade into the app. After 90 s with no answer, show a clear error with a Retry button.
- It must not flash at all when the server is already awake.
- Add `data-testid="wake-screen"`.

## B — Squashed pharmacist verify row at 390 px
On `/pharmacist` (verify queue, `src/app/pharmacist/page.tsx` ~line 110, the `row()` helper) the row squashes on a 390 px wide phone: long bilingual drug name + patient name wrap badly (see `docs/ppt-pack/screens/S08*`). Fix the layout so at 360, 390 and 420 px widths nothing overlaps, no text is cut mid-word, and the status badge stays readable. Check every other row list using the same helper.

## C2 — "Medicine arrived" notifications
The design already promises it (M-Case screen: "पहुँचते ही हम आपको बताएँगे / We'll tell you as soon as it's there").
Backend contract v0.7 (Codex is building it now — use exactly this):
- `GET /api/v1/notifications` → newest-first list of `{id, case_id, kind: "on_the_way"|"arrived"|"given", drug_id, facility_id, at, read, hi, en}` for the logged-in patient or ASHA.
- `POST /api/v1/notifications/{id}/read` → `{id, read: true}`.
Build:
- A bell in the patient and ASHA shells with an unread count badge (`data-testid="notif-bell"`, `notif-count`). Poll every 20 s while the page is visible.
- A notification list (sheet or page) showing each item's `hi`/`en` text and time; tapping one marks it read and opens its case (`/patient/cases/[id]`). `data-testid="notif-item-<id>"`.
- For an unread `arrived` notification, a prominent banner on the patient home: "आपकी दवा पहुँच गई / Your medicine has arrived" with the PHC name (`data-testid="arrived-banner"`).
- Add the two calls to `src/lib/api.ts` with types.
Until Codex's endpoint is live on your local backend, the screen must fail quietly (no bell count, no error toast) — never crash.

## E2 — Offline report, tested for real
Offline reporting exists (`src/lib/OfflineQueueContext.tsx`, used in `src/app/patient/report/page.tsx` and `pharmacist/stock`), but it has never been tested in a browser.
- Write `e2e/offline-asha.spec.ts`: reset demo → log in as ASHA → `context.setOffline(true)` → report for Ramesh by typing (not voice) → the app must clearly say it is saved on the phone and will send when online (`data-testid="saved-offline"`) → `context.setOffline(false)` → the queue flushes → log in as pharmacist → the new report is in the verify queue. Also assert the same report does not appear twice.
- While offline, the mic/voice button must be disabled with a bilingual note that voice needs internet.
- Fix any bugs this test exposes in the app code (e.g. the queue not flushing on reconnect, `isOffline` stale inside `enqueue`).

## Done means (paste all of this output into docs/notes-agy.md)
1. `npm run lint` → 0 errors. `npm test` → all pass. `npm run build` → success.
2. With the backend running locally (`cd backend && .venv/bin/uvicorn app.main:app --port 8000`) and the frontend running: `npx playwright test` → every spec passes, including the 2 old ones and your new one. Paste the final summary lines.
3. Screenshots at 390 px width saved to `e2e/shots/f3-*.png`: wake screen, pharmacist home, notification bell with count, notification list, arrived banner, offline "saved" state.
4. A list of every file you changed, and anything you could NOT finish — say it plainly.
