Continue as backend engineer (network allowed). Round 6 verified by Claude (67 passed; live transfer draft answered by gemini-3.1-flash-lite in 5.2 s). The frontend is being fixed by another agent in frontend/ right now — do NOT touch frontend/.

B20 — Live Hindi AUDIO test (the demo's core step; never tested with real audio):
1. First confirm in code what POST /cases/voice sends to Gemini: the raw audio bytes (inline audio part), or something else? If the audio is not actually sent to Gemini for transcription + extraction, fix that so it is (keep the deterministic fallback and ai_source).
2. Create 12 synthetic Hindi voice clips with Gemini TTS (model list includes gemini-3.8-flash-tts and gemini-3.1-flash-tts-preview; use whichever works), spoken like a rural patient/ASHA, e.g. "मेरी मेटफॉर्मिन की दवा ख़त्म हो गई, कल सुंदरपुर PHC गया था, दवा नहीं मिली, घर पर दो दिन की बची है". Vary medicine (the 4 seeded drugs), date words (कल, परसों, सोमवार), quantities, household days, include 2 negations ("दवा मिल गई थी") and 2 Hinglish clips. Store audio + expected fields in backend/eval/audio/synthetic/ (label everything synthetic).
3. Run every clip through the real POST /cases/voice path (TestClient, live Gemini) and score transcript sanity + each extracted field vs expected. Also score any real recordings Aditya drops into backend/eval/audio/real/ (file name = short id; expected fields in a same-name .json you create ONLY if he provides them — otherwise report transcript + fields for Claude to check by ear). Create that folder with a README telling him the format (.m4a/.webm/.wav, <20 s).
4. Report: calls ok/failed, model used, latency, per-field accuracy, every wrong field shown. Honest: TTS voice is easier than real speech — say so.

B21 — Submission drafts (write in docs/, plain English, every number must be traceable to our repo or PLAN.md sources; mark anything unverified with [VERIFY]):
- docs/README-draft.md: what Saathi is (2 lines), the Ramesh loop, how to run backend + frontend locally, demo users, architecture (FastAPI, OR-Tools, Gemini with fallback, Next.js, offline queue), safety rules, honest evaluation results (B10 table highlights incl. the over-forecast cost; live Gemini numbers), synthetic-data notice, roadmap.
- docs/description-draft.md: exactly 3 versions of a 2–3 line submission description.
- docs/video-script-draft.md: a 3.5-minute demo script with timestamps following the Ramesh story, what is on screen, and the voice-over lines (English, with one Hindi voice clip moment).

Rules: edit only backend/ and those docs files (plus notes-codex.md). Never print or log the key. ruff clean; full pytest green (paste the real final line). No commit, push, deploy.
