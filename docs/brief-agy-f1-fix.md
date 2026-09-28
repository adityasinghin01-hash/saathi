Claude (instructor) reviewed your F1 work. It FAILS review. Fix exactly these, then prove it:

1. `npm test` script missing → add `"test": "vitest run"` to frontend/package.json.
2. Vitest cannot start: `@vitejs/plugin-react` is ESM-only and vitest.config.ts is loaded as CJS. Fix (e.g. rename to vitest.config.mts or set "type": "module" safely) so `npm test` runs.
3. `npm run build` fails type check because vitest.config types (vite vs vitest's nested vite) conflict → exclude vitest.config.* and __tests__ from the Next tsconfig build, or align versions. Build must pass.
4. Lint: 11 errors, 8 warnings. Remove every `any` in src/lib/api.ts (use proper types from the CONTRACT), fix the react-hooks/immutability issue in src/lib/OfflineQueueContext.tsx (flushQueue used before declaration — use useCallback and correct dependency order), remove unused vars. `npm run lint` must show 0 errors, 0 warnings.
5. Hard-coded English text violates the bilingual rule. Move ALL of these (and any others you find) into en.json + hi.json with proper Hindi: RootLayoutClient.tsx ("Refill Loop", "English"), asha/page.tsx "Cases", pharmacist/page.tsx "Cases to Verify", "Other Cases", patient/page.tsx "Cases", patient/cases/[id]/page.tsx "Confirm Received", "Events", district/transfers/[id]/page.tsx "Approve", "Reject". Add a test that fails if any JSX text literal outside the i18n helper exists in src/app (simple scan is fine).
6. Write docs/notes-agy.md: what is done, how to run, and the REAL final output lines of `npm run lint`, `npm run build`, `npm test`.

Rules unchanged: edit only frontend/ and docs/notes-agy.md; no visual design work; no commit/push/deploy.
