# Live voice evaluation — 29 September 2026

All twelve `s01`–`s12` clips are **Synthetic demo data** made with Gemini TTS. `r01.opus` is a real human WhatsApp Ogg/Opus recording. Each file was posted as multipart audio to `POST /api/v1/cases/voice` through FastAPI TestClient with a live Gemini key; no case was confirmed or saved. The browser format `audio/webm` and WhatsApp `audio/ogg` are accepted by the route. The paced run used `GEMINI_MODELS=gemini-3.1-flash-lite .venv/bin/python -m eval.audio_eval --pause-seconds 15` from `backend/`. Exact responses are in [audio.json](audio.json); the standalone r01 retry is in [audio_r01_retry.json](audio_r01_retry.json). Neither file contains the provider key.

## Synthetic clips

All 12 calls returned HTTP 200 from live `gemini-3.1-flash-lite`, with no provider fallback. Patient ID came from demo authentication. Every drug ID, quantity, household supply, and attempted **UTC date** matched its hand-labeled script (12/12 for each field). All 12 transcripts contained Devanagari, passed the limited transcript sanity check, and preserved whether the script said the medicine was received. The exact attempted time was not scored; the prompt represents a spoken date without a time as `00:00:00Z`.

| Clip | Returned patient | Returned drug / requested / home days / attempted date | Field match | Devanagari | Latency |
| --- | --- | --- | --- | --- | ---: |
| s01 | patient-003 | metformin / 30 / 2 / 2026-09-28 | 4/4 | yes | 4.56 s |
| s02 | patient-003 | glimepiride / 20 / 0 / 2026-09-27 | 4/4 | yes | 2.96 s |
| s03 | patient-006 | amlodipine / 15 / 3 / 2026-09-28 | 4/4 | yes | 12.53 s |
| s04 | patient-006 | telmisartan / 10 / 1 / 2026-09-28 | 4/4 | yes | 4.62 s |
| s05 | patient-003 | metformin / 25 / 4 / 2026-09-27 | 4/4 | yes | 7.23 s |
| s06 | patient-003 | glimepiride / 30 / 1 / 2026-09-28 | 4/4 | yes | 2.90 s |
| s07 | patient-006 | amlodipine / 12 / 0 / 2026-09-28 | 4/4 | yes | 5.99 s |
| s08 | patient-006 | telmisartan / 24 / 2 / 2026-09-27 | 4/4 | yes | 6.50 s |
| s09 | patient-003 | metformin / 20 / 4 / 2026-09-28 | 4/4 | yes | 4.16 s |
| s10 | patient-006 | amlodipine / 18 / 3 / 2026-09-28 | 4/4 | yes | 9.32 s |
| s11 | patient-003 | glimepiride / 16 / 2 / 2026-09-28 | 4/4 | yes | 5.37 s |
| s12 | patient-006 | telmisartan / 30 / 5 / 2026-09-27 | 4/4 | yes | 5.37 s |

The `s09` and `s10` transcripts say the medicine **was received**; both still describe a refill attempt. Gemini returned `not_a_refill_report: false` for all twelve clips, including those two. Mean API latency was 5.96 seconds. The scripts and exact gold fields are in [the synthetic audio folder](../audio/synthetic/).

## Real recording r01

The human label supplied for `r01.opus` is **not a refill report**. It is a general complaint about blood pressure, diabetes, and doctors. No drug, requested quantity, household supply, or attempted refill time was spoken. The expected response is `not_a_refill_report: true` and `null` for all four **audio-extracted** fields; `patient_id` remains `patient-003` from the chosen demo login under contract v0.6. The Hindi transcript should use Devanagari, while English words may remain in Latin.

| r01 call | HTTP / source | Classification | Audio-extracted fields | Transcript | Latency |
| --- | --- | --- | --- | --- | ---: |
| Paced run after 12 synthetic calls | 200 / fallback | unavailable | all null | unavailable | 9.53 s |
| Standalone live retry | 200 / Gemini 3.1 Flash Lite | `true`, matches gold | all null, matches gold | Devanagari, matches gold | 10.33 s |

The standalone retry returned `missing: ["drug_id", "requested_qty", "household_supply_days", "attempted_at"]`. Its transcript includes “हमारी तो तबीयत बहुत खराब है जी डॉक्टर जी हमारी सुनते ही नहीं है” and contains no refill request. The full returned transcript and fields are in [audio_r01_retry.json](audio_r01_retry.json). The paced run's fallback had no transcript or classification evidence, so it is not counted as a successful real-audio extraction. That run started before the final fallback classification change; the current fallback returns `not_a_refill_report: null` rather than asserting a classification.

## Limits

TTS is cleaner than spontaneous phone speech, and twelve scripted clips do not establish field accuracy for real patients. The transcript sanity score is a character or spoken-fact proxy, not word error rate. The r01 result is one labeled real recording and one successful live retry; the earlier fallback is reported separately. Case creation still requires human-confirmed, non-null fields.
