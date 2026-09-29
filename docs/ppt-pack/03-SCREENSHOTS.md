# Screenshot map

These files are in `docs/ppt-pack/screens/`. They show **Synthetic demo data**. Keep that label visible when cropping a screen; if a crop removes the app badge, add the exact label beside the image. Screen values, case IDs and timestamps are one seeded demo run. They are not forecast evaluation or field results. **Ignore S21**: its filename says Hindi-first, but it duplicates the patient-home view and is not a Hindi-first screen.

| File | What it shows | Best slide / use |
|---|---|---|
| [S01-landing-top.png](screens/S01-landing-top.png) | Saathi logo, bilingual landing hero, refill promise | 1 title; 12 closing |
| [S02-landing-full.png](screens/S02-landing-full.png) | Full landing page and explanation of the loop | 1 optional background/reference; crop one section only |
| [S03-login-roles.png](screens/S03-login-roles.png) | Synthetic demo role picker for patient, ASHA, pharmacist and officer | 4 role context; 8 demo-login limitation |
| [S04-patient-home.png](screens/S04-patient-home.png) | Ramesh's patient home and refill entry point | 4 or 5 opening inset |
| [S05-patient-voice.png](screens/S05-patient-voice.png) | Patient microphone screen and type-instead option | 6 voice entry |
| [S06-patient-check-details.png](screens/S06-patient-check-details.png) | Extracted transcript and editable confirmation fields | 6 human read-back; 9 safety |
| [S07-patient-case-reported.png](screens/S07-patient-case-reported.png) | Case after report, awaiting staff verification | 4 or 5; label **reported**, not confirmed stockout |
| [S08-pharmacist-home.png](screens/S08-pharmacist-home.png) | Pharmacist's pending work and stock context | 2 small workflow context; 5 before verification |
| [S09-pharmacist-verify.png](screens/S09-pharmacist-verify.png) | Sunita checks the on-hand count and confirms the stockout | 5 main sequence; 9 trust gate |
| [S10-district-overview.png](screens/S10-district-overview.png) | District summary, warnings and Ramesh action | 8 architecture in use; 3 small context |
| [S11-district-overview-full.png](screens/S11-district-overview-full.png) | Full district stock table and warnings | 8 or 3, crop table with stock age and both demand columns |
| [S12-district-facility-chart.png](screens/S12-district-facility-chart.png) | Facility stock/need history chart | 3 hidden-demand example; not the evaluation chart |
| [S13-transfer-ai-draft.png](screens/S13-transfer-ai-draft.png) | Nayagaon → Sundarpur proposed transfer, constraints and approval button | 5, 6 and 9; crop the checks with officer approval |
| [S14-patient-case-on-the-way.png](screens/S14-patient-case-on-the-way.png) | Ramesh sees medicine on the way | 5 optional progress step |
| [S15-pharmacist-received.png](screens/S15-pharmacist-received.png) | Sunita records medicine received at the centre | 5 optional; distinguish centre receipt from patient supply |
| [S16-pharmacist-hand-over.png](screens/S16-pharmacist-hand-over.png) | Sunita hands the medicine to Ramesh | 5 penultimate step |
| [S17-patient-closed.png](screens/S17-patient-closed.png) | Ramesh confirms receipt; case closes | 5 final step; 12 closing |
| [S18-district-audit-trail.png](screens/S18-district-audit-trail.png) | Full case-event history from report to closure | 5 inset; 9 audit proof |
| [S19-district-evaluation.png](screens/S19-district-evaluation.png) | UI view of forecast evaluation | 7 optional screenshot; write measured numbers from `backend/eval/results/forecast.md`, not from a crop |
| [S20-asha-patients.png](screens/S20-asha-patients.png) | Rekha's assigned patient list and “Report for a patient” entry | 4 ASHA role; 10 assisted-use point |
| [S22-asha-recording-voice.png](screens/S22-asha-recording-voice.png) | Rekha records for Ramesh; Hindi/English labels and recording state | 5 or 6 voice step |
| [S23-asha-voice-heard-hindi.png](screens/S23-asha-voice-heard-hindi.png) | Hindi transcript, AI draft badge, editable check screen and “Confirm & send” | 5 or 6. It shows Hindi speech in an English UI, not a Hindi-first interface |

**Preferred story strip for slide 5:** S23 → S09 → S13 → S16 → S17, with D5 as the status line. S18 is a close-up on slide 9. Use a visible “Synthetic demo data” label even when these mobile crops do not show the header badge.
