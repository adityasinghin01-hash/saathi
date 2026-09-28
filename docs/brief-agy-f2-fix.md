Your Ramesh e2e test is NOT valid, and the story does NOT work in the browser. Claude ran it against the real backend (DEMO_MODE=1 uvicorn on :8000 + npm run dev):
- It FAILS: timeout waiting for input[type="number"] on /pharmacist/verify/<caseId>. That page renders an EMPTY <main> (header shows, no case, no form). The UI language was also Hindi, not English.
- The test has ZERO expect() calls. Every later step is wrapped in `if (caseId)` or `if (await x.isVisible())`, so a broken step is silently skipped and the test still "passes". It uses a hard-coded 'transfer-1' id and fixed waitForTimeout sleeps. Only 4–6 screenshots were ever produced, so the story never got past the pharmacist.

Fix, in frontend/ only (do not touch backend/):
1. Make every screen of the story actually work against the real backend (shapes in docs/api-examples.md): pharmacist verify page, officer draft → review → approve → dispatch (use the transfer id the API returns, never a guessed id), pharmacist receive + give 30, patient "I got my medicine".
2. Rewrite e2e/ramesh.spec.ts as a REAL test:
   - NO `if` around steps, NO isVisible() guards, NO waitForTimeout, NO hard-coded ids. Read ids from the page or from the API responses (page.waitForResponse).
   - After EVERY step, expect() the visible result, e.g. status text "Reported", "Verified", "Transfer drafted", "Approved", "Dispatched", "Received", "Supplied", "Closed" (or their t() equivalents) and a final check via the API: GET /api/v1/cases/{id} with header X-Demo-User: officer-1 → status "closed".
   - Force English by setting the language in the app (localStorage/cookie your app uses) before the first page load; do not rely on defaults.
   - A screenshot after every step: 10+ files in e2e/screenshots/.
   - Add a playwright.config.ts (baseURL http://localhost:3000, one worker, trace on failure).
3. Run with both servers up and paste the REAL output of: npm run lint, npm run build, npm test, npx playwright test. The Playwright line must show "1 passed" AND the screenshots folder must hold 10+ files. List the screenshot filenames in docs/notes-agy.md.

If a step cannot work because the backend behaves differently from docs/api-examples.md, STOP and write exactly what you sent and what came back in docs/notes-agy.md under "Backend question" — do not work around it and do not skip it.
