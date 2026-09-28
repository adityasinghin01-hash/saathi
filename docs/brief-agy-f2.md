You are the frontend engineer for Saathi in ~/dev/refill-loop. Edit ONLY frontend/ and docs/notes-agy.md. Do not touch backend/ or any other docs file.

READ FIRST: docs/CONTRACT.md (especially "v0.4") and docs/api-examples.md. api-examples.md holds REAL responses from our backend. Your TypeScript types and API calls must match those exact JSON shapes — do not guess any field.

GOAL: every screen of the Ramesh story WORKS against the real backend, in plain styling (keep the current look; the final design comes later, so no styling work). Every visible string goes through t(...) with en + hi entries.

A. Fix what the review found in F1
1. POST /sync/batch body must be {"ops":[...]}, not a bare list.
2. GET /district/overview returns a FLAT LIST of rows (facility × drug). Fix the type and group it in the UI.
3. Add the missing API calls: POST /cases/voice (multipart: audio file + lang), POST /demo/reset, GET /demo/scenario/ramesh, GET /evaluation/summary, POST /cases/{id}/cancel.
4. Extend the "no hard-coded text" test to src/components too, and to placeholder / aria-label / title / alt attributes.

B. Build the Ramesh story screens (plain, working)
Patient (demo user patient-user-001) + ASHA (asha-1):
- Home: my medicines + a big "Medicine not received" button.
- Voice report: record with the browser mic (MediaRecorder) → POST /cases/voice → show transcript + extracted fields in an editable form → Confirm → POST /cases/voice/confirm. Also a "type instead" path using POST /cases. Show a badge when ai_source is not "gemini": "Drafted by rules — AI unavailable".
- My case: status timeline built from the case's events (GET /cases/{id}), and a "I got my medicine" button (confirm-received-by-patient) when the status allows it.
- ASHA: list of my patients → pick one → the same report flow on their behalf.
Pharmacist (pharmacist-1):
- Verify queue (GET /cases?status=reported) → verify screen (result + on_hand).
- Incoming transfers → Receive; then Give to patient with a quantity (partial allowed; show given / asked).
- Stock update form (use the exact body shown in api-examples.md for POST /stock).
District officer (officer-1):
- Overview table: rows = PHC × medicine with on hand, data age (from recorded_at), patients' need, dispensing forecast, days left, warning, open cases; sort + filter.
- Facility × drug detail with a simple chart (need vs forecast vs stock).
- Transfer draft review: donor, quantity, batches + expiry, the 3 constraint checks, rationale, "Drafted by AI — needs your approval" badge, Approve / Reject (with note). Handle the no_feasible_transfer result. Then Dispatch.
- Case board grouped by status, with the audit trail (events) of a case.
- Evaluation page from GET /evaluation/summary, labelled "Synthetic simulation — not real patients".
Everywhere: loading, empty and error states; the "Synthetic demo data" badge; the offline queue still works.

C. A demo helper on the login page (only when NEXT_PUBLIC_DEMO_MODE=1): "Reset demo" (POST /demo/reset) and one-click login buttons for the four Ramesh-story users.

D. PROVE IT — mandatory, with real output pasted into docs/notes-agy.md:
1. Start the backend: cd backend && DEMO_MODE=1 .venv/bin/uvicorn app.main:app --port 8000 (do not change backend code).
2. Write a Playwright test (frontend/e2e/ramesh.spec.ts) that plays the WHOLE story in the browser against that backend: reset → patient reports via "type instead" → pharmacist verifies out of stock → officer drafts transfer, approves, dispatches → pharmacist receives and gives 30 → patient confirms → case shows "closed". Take a screenshot at every step into frontend/e2e/screenshots/.
3. npm run lint, npm run build, npm test, npx playwright test — all must pass. Paste the real final lines of each.

Do not claim anything is done unless its command output is pasted. Do not commit, push or deploy.
