`POST /api/v1/cases/voice` already sent the uploaded **raw audio bytes** to Gemini as an inline audio part. I kept that path and its marked deterministic fallback. The live test exposed a timestamp bug: Gemini returned valid UTC as `+00:00`, which the backend rejected. The parser now accepts it and returns `Z`. See [voice.py](/Users/aditya/dev/refill-loop/backend/app/api/voice.py) and [ai.py](/Users/aditya/dev/refill-loop/backend/app/domain/ai.py).

I generated 12 labeled synthetic Hindi TTS clips and posted all 12 through the real route. All returned HTTP 200; **9 received live Gemini answers and 3 used fallback**. All live answers used `gemini-3.1-flash-lite`. Mean latency was **9.46 s** for live answers and **14.85 s** across all calls. Among the nine live answers, medicine, quantity, and household days were each **9/9** correct; attempted date was **8/9**. Transcript sanity checks passed for **9/9** live answers, including two returned in romanized Hindi.

Every first-pass field mismatch was:

| Clip | Wrong fields: expected → returned |
| --- | --- |
| s08, live | Date: Sep 27 → Sep 28 |
| s09, fallback | Quantity: 20 → 30; household days: 4 → 0 |
| s10, fallback | Quantity: 18 → 30; household days: 3 → 0 |
| s12, fallback | Medicine: telmisartan → amlodipine; household days: 5 → 0; date: Sep 27 → Sep 28 |

The two “दवा मिल गई थी” clips succeeded with correct fields on separate paced live retries; `s12` fell back again. A separate live check using Ramesh’s demo login returned the expected metformin fields. Full transcripts, per-clip latencies, scores, and retries are in [audio.md](/Users/aditya/dev/refill-loop/backend/eval/results/audio.md) and [audio.json](/Users/aditya/dev/refill-loop/backend/eval/results/audio.json).

The [real-recording folder](/Users/aditya/dev/refill-loop/backend/eval/audio/real/README.md) has format and labeling instructions, but contained **no real recordings** to score. TTS speech is cleaner than spontaneous patient speech, so these results do not establish real-speech accuracy.

The submission drafts are [README-draft.md](/Users/aditya/dev/refill-loop/docs/README-draft.md), [description-draft.md](/Users/aditya/dev/refill-loop/docs/description-draft.md), and [video-script-draft.md](/Users/aditya/dev/refill-loop/docs/video-script-draft.md). Frontend browser behavior remains marked `[VERIFY]` while that work continues.

Final checks: Ruff — `All checks passed!` Full pytest — **`74 passed, 1 skipped, 1 warning in 27.41s`**. No commit, push, or deploy was performed.