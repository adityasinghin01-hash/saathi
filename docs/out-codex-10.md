Implemented the v0.6 voice changes. Unspoken refill fields now return `null` with a `missing` list; non-refill speech returns `not_a_refill_report: true`. The deterministic fallback returns null fields with `ai_source: "fallback"`. Both case creation routes reject null required fields with a field-specific 422.

The [audio results](/Users/aditya/dev/refill-loop/backend/eval/results/audio.md) record live Gemini answers for all 12 synthetic clips, with all scored fields matching. The paced r01 call fell back; a [standalone live retry](/Users/aditya/dev/refill-loop/backend/eval/results/audio_r01_retry.json) classified it as **not a refill report**, returned a Devanagari transcript, and left all four speech-derived fields null. Per the v0.6 contract, `patient_id` remains filled from login. [API examples](/Users/aditya/dev/refill-loop/docs/api-examples.md) were regenerated.

Ruff: `All checks passed!`  
Full pytest final line: `100 passed, 1 skipped, 1 warning in 55.36s`

No commit, push, or deploy was performed.