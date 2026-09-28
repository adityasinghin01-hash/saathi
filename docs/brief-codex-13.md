You now own the remaining work on Saathi (Code for Communities, Track 3, due Wed 30 Sep 2026). Claude built the frontend (frontend/, Next.js 16 — read frontend/AGENTS.md; designed with the Saathi system in src/styles) and it is verified: `npx playwright test` passes BOTH e2e/ramesh.spec.ts (full story) and e2e/voice-asha.spec.ts (ASHA + Hindi voice via fake mic) with backend `DEMO_MODE=1 .venv/bin/uvicorn app.main:app --port 8000` and `npm run dev`. Keep them passing after every change: run `npm run lint`, `npm test`, `npm run build`, and both Playwright tests, and paste the real final lines.

Tasks, in order:
1. Frontend deploy readiness (do NOT deploy): NEXT_PUBLIC_API_BASE and NEXT_PUBLIC_DEMO_MODE documented; a short docs/DEPLOY.md with exact click-by-click steps for Render (backend, uses backend/render.yaml; set GEMINI_API_KEY + ALLOWED_ORIGINS=<vercel url>) and Vercel (root = frontend/, env vars) written for a beginner.
2. README.md at repo root from docs/README-draft.md: run instructions, demo users, architecture, safety rules, honest evaluation (use numbers from backend/eval/results/*.md and docs/notes-codex.md only; every number must be traceable — mark anything else [VERIFY]), voice results (12 synthetic TTS clips + 1 real WhatsApp clip classified as not-a-refill-report; say plainly real speech is barely tested), synthetic-data notice, roadmap from ~/dev/c4c2-ideas/PLAN.md.
3. docs/description-final.md: best 2–3 line description.
4. docs/deck-outline.md: 11 slides, each with title, 3–5 bullet facts (sourced), and which screenshot from frontend/e2e/shots/ to use.
5. docs/video-shotlist.md: 3.5-min shot list matching the real screens and data-testids, with the Hindi voice moment (note: Gemini voice takes ~5–15 s; plan a cut).
6. Update docs/HANDOFF.md "State" with what you did and what is left.
Rules: never print the Gemini key; do not commit, push or deploy (Aditya must say yes first). Stop and write questions in docs/notes-codex.md if anything is unclear.
