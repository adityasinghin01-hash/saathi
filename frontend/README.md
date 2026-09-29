# Saathi frontend

Next.js frontend for the synthetic Saathi refill demo. Run the [backend](../backend/README.md) first, then from `frontend/`:

```sh
npm ci
NEXT_PUBLIC_DEMO_MODE=1 npm run dev
```

Open `http://localhost:3000`. The app calls `http://localhost:8000` unless `NEXT_PUBLIC_API_BASE` is set.

| Variable | Example | Effect |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE` | `https://your-backend.onrender.com` | Browser-visible backend **origin**, without `/api/v1` or a trailing slash. Defaults to `http://localhost:8000`. |
| `NEXT_PUBLIC_DEMO_MODE` | `1` | Shows the **Reset demo** button on `/login`. Set it to `1` for the synthetic demo; the backend also needs `DEMO_MODE=1` for reset to work. |

Both `NEXT_PUBLIC_` values are included in the browser build. Set them before building or deploying; rebuild after changing either. Do not put `GEMINI_API_KEY` here or in any frontend variable. The backend holds that secret.

From this directory, run `npm run lint`, `npm test`, and `npm run build`. With both local servers running and backend `DEMO_MODE=1`, run `npx playwright test e2e/ramesh.spec.ts e2e/voice-asha.spec.ts`. The voice test feeds a labeled synthetic Hindi clip into Chromium's fake microphone and calls the real backend voice route.

For hosted setup, see [the deployment guide](../docs/DEPLOY.md). Demo login uses selectable synthetic users, not passwords or production authentication.
