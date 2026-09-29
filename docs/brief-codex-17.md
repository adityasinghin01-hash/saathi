# Codex round 17 — README, description, app icon (29 Sep 2026)

Repo root = this folder. Read docs/HANDOFF.md (top "UPDATE 29 Sep ~12 PM" section), docs/CONTRACT.md (v0.7), README.md, docs/description-final.md first.
Do not commit, push or deploy. Do not touch backend/app or frontend/src logic. Write your report to docs/out-codex-17.md.

The app is LIVE and the repo is PUBLIC: judges will read the README first.
Live app: https://saathi-drab.vercel.app · API: https://saathi-api-gm4i.onrender.com (free plan, sleeps; the app shows a "waking up" screen) · Repo: https://github.com/adityasinghin01-hash/saathi

## 1 — README.md rewrite (keep every honest limit that is already there)
Order:
1. Title + one plain sentence of what it does + **Live demo** link + a line: "Free server: first load can take up to a minute; the app shows a waking-up screen."
2. **The problem** in 3 lines. Use ONLY numbers from ~/dev/c4c2-ideas/PLAN.md §12 (verified), with their source names. No new numbers.
3. **Try it in 2 minutes**: the four demo logins (Ramesh patient, Rekha ASHA, Sunita pharmacist, Dr. Mehra district officer) and the exact click path of Ramesh's story, incl. Reset demo.
4. **Features (shipped)** — a table: feature · who uses it · one plain line. Must include: Hindi voice report with read-back + manual form; ASHA reports for her patients; pharmacist verify (report vs confirmed stock-out); district overview (cohort need vs dispensing forecast, days left, warnings); OR-Tools transfer draft + Gemini rationale + officer approval; dispatch/receive/hand-over/close with full audit trail; **"medicine arrived" alerts** (bell, list, arrived banner — new, /notifications, contract v0.7); **offline reporting** (saved on phone, sent on reconnect, never twice, refused reports flagged — new); **waking-up screen** (new); bilingual Hindi+English UI everywhere; demo reset; evaluation page.
5. **How it works** — the loop in one short numbered list + a mermaid diagram (patient/ASHA → pharmacist → district → transfer → PHC → patient).
6. **Tech**: FastAPI + SQLite, Next.js PWA, Gemini (voice + rationale), OR-Tools, IndexedDB offline queue, Render + Vercel. One line each.
7. **Tests**: backend pytest count (run it: `cd backend && .venv/bin/pytest -q`, report the real number), 3 Playwright browser stories (ramesh, voice-asha, offline-asha) with the live-run command from HANDOFF. State they passed against live on 29 Sep 2026.
8. **Honest evaluation** — keep the existing section's numbers and caveats accurate (re-check every number against backend/eval/results/*.md; fix any mismatch).
9. **Safety and data limits** — keep existing.
10. **Roadmap** — from PLAN.md §0.6 phases 1–5, one line each, clearly "not built".
11. Run locally — keep existing.
Plain English, short sentences, no marketing words ("revolutionary", "seamless"). Every relative link must resolve to a real file (check each one).

## 2 — docs/description-final.md
2–3 lines, ≤ 60 words total, for the submission form. Must say: who (patients + ASHA workers, government PHCs, diabetes/BP), what (Hindi voice report of a missed refill → pharmacist check → AI-drafted, officer-approved stock transfer → "medicine arrived" alert → closed), and that it is a live synthetic prototype. Write 2 variants below the main one, labelled.

## 3 — App icon + install settings (frontend/public only)
- `/icon.png` is referenced by frontend/public/manifest.json but does not exist (404 on the live site).
- Make `frontend/public/icon-192.png`, `icon-512.png`, and `apple-touch-icon.png` (180) from `frontend/public/art/logo.svg` (render with Python: cairosvg or pillow; install into a throwaway venv if needed). Terracotta mark centred on the Saathi paper background, safe padding for maskable.
- Update manifest.json: name "Saathi · साथी", short_name "Saathi", theme/background colours from the tokens in frontend/src/styles (the paper + clay values), icons 192 + 512 (one `purpose: "any maskable"`).
- Add the apple-touch-icon + theme-color to the Next.js metadata only if it is a one-line change in the root layout; say what you changed.
- Check there are no other references to "Refill Loop" in user-visible frontend text or metadata; list them (fix only metadata/manifest).

## Done means
List every file changed. Paste the pytest summary. Say plainly anything not done.
