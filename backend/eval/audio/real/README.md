# Real audio drop folder

Put recordings here as `<short-id>.m4a`, `<short-id>.webm`, `<short-id>.wav`, or WhatsApp Ogg/Opus `<short-id>.opus`, each shorter than 20 seconds. Use a short anonymous ID as the filename; do not put names or phone numbers in it. These are real recordings, not synthetic demo data.

Run `PYTHONPATH=. .venv/bin/python -m eval.audio_eval` from `backend/`. The evaluator sends each file through the real `POST /api/v1/cases/voice` route. It uploads `.opus` as `audio/ogg`, `.webm` as `audio/webm`, and converts `.m4a` to WAV with macOS `afconvert` or, elsewhere, `ffmpeg`. It uses `patient-user-003` by default, whose active medicines are metformin and glimepiride. For amlodipine or telmisartan clips without labels, pass `--real-user-id patient-user-006` in a separate run.

Only add a same-name `<short-id>.json` when Aditya has provided the expected fields. Never infer a gold label from Gemini's answer. The JSON can contain `user_id`, `lang`, `patient_id`, `expected_not_a_refill_report`, and `expected_fields` with `patient_id`, `drug_id`, `requested_qty`, `household_supply_days`, and `attempted_date` (YYYY-MM-DD or null). Unlabelled clips are skipped and listed. See [RECORDING-GUIDE.md](RECORDING-GUIDE.md) for the six-clip recording brief.
