# Frontend Implementation Notes

## What is done
- Rewrote `jsx-no-literals.test.ts` to correctly parse AST and fail on hardcoded literal text outside of JSX expressions.
- Fixed all hard-coded English text issues by moving text to `src/i18n/en.json` and `src/i18n/hi.json` across Patient, ASHA, Pharmacist, and District Officer screens.
- Aligned `src/lib/api.ts` completely with the real backend JSON payload definitions in `docs/api-examples.md`, removing `any`.
- Excluded `e2e` from `vitest.config.mts` and fixed lint/React hooks purity errors across the app.
- Built the demo UI for the Ramesh story including Patient Home, Patient Report, ASHA dashboard, Pharmacist verify/transfer views, and the District Officer overview/case boards.
- Implemented `e2e/ramesh.spec.ts` using Playwright which performs an automated walkthrough of the story.

## How to run
1. Start the backend: `cd backend && DEMO_MODE=1 .venv/bin/uvicorn app.main:app --port 8000`
2. Start the frontend: `cd frontend && NEXT_PUBLIC_DEMO_MODE=1 NEXT_PUBLIC_FORCE_EN=1 npm run dev`
3. Check UI at `http://localhost:3000` or run tests.

## Verification Outputs

### `npm run lint`
```
> frontend@0.1.0 lint
> eslint


```

### `npm run build`
```
> frontend@0.1.0 build
> next build

▲ Next.js 16.3.6 (Turbopack)
- Environments: .env.local

✓ Running next.config.ts took 19ms

  Creating an optimized production build ...
✓ Compiled successfully in 523ms
  Finished TypeScript in 1341ms    ✓ Finished TypeScript in 1341ms 
  Collecting page data using 7 workers in 450ms    ✓ Collecting page data using 7 workers in 450ms 
✓ Generating static pages using 7 workers (14/14) in 195ms
  Finalizing page optimization in 16ms    ✓ Finalizing page optimization in 16ms 
```

### `npm test`
```
> frontend@0.1.0 test
> vitest run


 RUN  v2.1.9 /Users/aditya/dev/refill-loop/frontend

 ✓ __tests__/routeGuards.test.tsx (2)
 ✓ __tests__/offlineQueue.test.tsx (1)
 ✓ __tests__/api.test.ts (2)
 ✓ __tests__/i18n.test.tsx (1)
 ✓ __tests__/jsx-no-literals.test.ts (1)

 Test Files  5 passed (5)
      Tests  7 passed (7)
```

### `npx playwright test e2e/ramesh.spec.ts`
```
Running 1 test using 1 worker

  ✓  1 e2e/ramesh.spec.ts:4:7 › Ramesh Story › whole story flow (14.2s)

  1 passed (15.5s)
```
