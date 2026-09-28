You are the frontend engineer. Claude is the instructor and will review every file you write.
Read docs/CONTRACT.md and docs/TASKS.md fully. Do task F1 only.

Rules:
- Edit ONLY inside frontend/ (plus docs/notes-agy.md). Never touch backend/ or docs/CONTRACT.md.
- NO visual design work: plain, minimal default styling only. The real design comes later from Claude Design.
- Every user-visible string must exist in BOTH hi.json and en.json. No hard-coded text in components.
- Follow the CONTRACT exactly (paths, field names, status values). If something is unclear, write the question in docs/notes-agy.md and continue with the most conservative choice marked `ASSUMPTION`.
- Backend runs at http://localhost:8000 (env NEXT_PUBLIC_API_BASE). Do not start or modify it.
- Run `npm run lint`, `npm run build`, and `npm test` at the end; all must pass. Paste the real output summaries into docs/notes-agy.md.
- Do not commit, push or deploy.

End by writing docs/notes-agy.md: what is done, how to run, test/lint/build results, open questions, assumptions.
