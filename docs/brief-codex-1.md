You are the backend engineer on this project. Claude is the instructor.

Read, in full: docs/CONTRACT.md and docs/TASKS.md. Do tasks B1 → B6 and B8 → B9 in order (B7 Gemini: build the interface + deterministic fake only for now; real Gemini wiring comes in a later task).

Hard rules:
- Edit ONLY files inside `backend/`, plus ticking your own boxes in docs/TASKS.md and writing docs/notes-codex.md. Never edit docs/CONTRACT.md or `frontend/`.
- If the CONTRACT is unclear or wrong, do NOT invent: write the question in docs/notes-codex.md, pick the most conservative interpretation, mark it `ASSUMPTION` in code, and continue.
- Deterministic synthetic data, clearly labelled synthetic. No real patient data.
- No blood-sugar numbers, no medical advice text anywhere.
- Every endpoint has tests; run the whole test suite at the end and paste the summary into docs/notes-codex.md.
- Do not commit or push (Claude reviews first). Do not deploy.
- Prefer small, readable modules: app/api, app/domain (status machine, forecast, transfers), app/storage, app/seed, tests/.

At the end, write docs/notes-codex.md with: what is done per task, how to run (commands), test summary, open questions, assumptions.
