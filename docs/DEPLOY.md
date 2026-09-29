# Deploy Saathi after Aditya approves

This is a click guide, not a deployment record. First commit and push the reviewed repository to a Git provider. Keep `backend/.env` and all keys out of Git. Render hosts the API; Vercel hosts the Next.js frontend. Both services must use HTTPS.

## Render: backend

1. Sign in to [Render](https://dashboard.render.com/). Click **New → Blueprint** and connect the repository.
2. Select the pushed branch. In **Blueprint Path**, enter `backend/render.yaml` (the file is not at the repository root). Review the proposed `refill-loop-backend` web service. The Blueprint sets Python, the backend root, build/start commands, `DEMO_MODE=1`, and `/api/v1/health`.
3. When Render prompts for the `GEMINI_API_KEY` secret, paste it into Render's secret field. Never paste it into Git, Vercel, a screenshot, or a support message. Click **Deploy Blueprint**.
4. On the service page, copy its `https://…onrender.com` URL. Open `<render-url>/api/v1/health` in a browser and check that it returns `status: ok`. Use this URL as the Vercel API base, without `/api/v1`.

The first Render deploy can use the Blueprint's default CORS origin (`http://localhost:3000`). Finish the Vercel steps, then return here to add the actual Vercel origin:

5. In Render, open the backend service → **Environment** → **Add Environment Variable**. Set `ALLOWED_ORIGINS` to the exact Vercel origin, for example `https://saathi-demo.vercel.app` (no path or trailing slash). For more than one trusted frontend origin, use a comma-separated list. Select **Save, rebuild, and deploy**.
6. Reopen the Vercel app after Render reports the service live. A failed browser request with a CORS error usually means the origin in `ALLOWED_ORIGINS` differs from the address bar; update it and redeploy Render.

Render's default SQLite store is a synthetic demo store. It can be lost on service replacement/restart without persistent storage; startup seeds an empty store. `DEMO_MODE=1` enables the destructive **Reset demo** action. Do not enter real patient information. See [Render Blueprints](https://render.com/docs/infrastructure-as-code) and [Render environment variables](https://render.com/docs/configure-environment-variables).

## Vercel: frontend

1. Sign in to [Vercel](https://vercel.com/new), click **Add New → Project**, and import the same repository and branch.
2. Set **Root Directory** to `frontend/` (use the directory picker; the repository root is not the Next.js app). Confirm the detected framework is **Next.js**.
3. Before clicking **Deploy**, add these **Environment Variables** for **Production**:

   | Name | Value |
   | --- | --- |
   | `NEXT_PUBLIC_API_BASE` | The Render URL from above, e.g. `https://refill-loop-backend.onrender.com` — no `/api/v1` or trailing slash. |
   | `NEXT_PUBLIC_DEMO_MODE` | `1` |

4. Click **Deploy**. Copy the deployment's stable production `https://…vercel.app` origin. Put that exact origin into Render's `ALLOWED_ORIGINS` using step 5 above.
5. Open the Vercel URL → **Open demo** → **Reset demo** → choose a demo role. If you later change a `NEXT_PUBLIC_` value, open the Vercel project → **Settings → Environment Variables**, edit it, then open **Deployments → ⋯ → Redeploy**; public values are fixed at build time.

For preview deployments, add the corresponding preview origin to `ALLOWED_ORIGINS` and set Vercel variables for **Preview** as well. Keep `GEMINI_API_KEY` only on Render. See [Vercel Git deployments](https://vercel.com/docs/git), [Vercel environment variables](https://vercel.com/docs/environment-variables), and [Next.js public variables](https://nextjs.org/docs/app/guides/environment-variables).
