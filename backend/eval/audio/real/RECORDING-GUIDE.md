# Six real Hindi refill voice notes

Ask 2–3 different people, if possible, to send six short WhatsApp voice notes. Each person should describe a **pretend** refill problem in their own Hindi words, as if talking to the PHC. Do not give them a script. Keep each clip under 20 seconds. Get their permission to use the recording in this local test, and use anonymous filenames `r02`–`r07` (for example, `r02.opus`). Do not put names or phone numbers in filenames or speech.

Give each speaker just one situation:

1. Your BP tablet ran out; you went to the PHC yesterday and were told to come next week.
2. You asked for metformin today, but the PHC had none; you still have two days of tablets at home.
3. Your glimepiride is nearly finished; you visited the PHC on Monday and received only some of what you asked for.
4. You went for amlodipine last week; the shelf was empty and you went home without tablets.
5. You need a telmisartan refill; the PHC asked you to return tomorrow.
6. You asked for your diabetes tablet at the PHC, but cannot remember how many tablets you requested or the exact day.

After listening to each recording, put a same-name JSON label beside it, such as `r02.json`. Use `r01.json` as the format example. Set `expected_not_a_refill_report` to `false`; `lang` to `hi`; `user_id` to `patient-user-003` for metformin or glimepiride, or `patient-user-006` for amlodipine or telmisartan. In `expected_fields`, write `patient_id` (`patient-003` or `patient-006`), the spoken `drug_id`, `requested_qty`, `household_supply_days`, and `attempted_date` (`YYYY-MM-DD`). Use `null` for any fact the speaker did not actually say; do not infer an answer from the situation or from Gemini. Leave `r01` labelled as a real, non-refill clip.

From `backend/`, run:

```sh
PYTHONPATH=. .venv/bin/python -m eval.audio_eval
```

The evaluator sends only clips with matching JSON labels. It lists unlabelled clips as skipped in the terminal and in `eval/results/audio.json`.
