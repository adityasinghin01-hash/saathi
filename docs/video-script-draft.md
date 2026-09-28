# Saathi demo video — draft, 3:30

Use the synthetic Ramesh scenario from [`play_ramesh.py`](../backend/scripts/play_ramesh.py). Reset the demo database before recording. The Hindi moment uses the **synthetic Gemini TTS** `s01.wav` clip, labeled on screen. [VERIFY: final screen order and browser behavior after frontend fixes.]

| Time | On screen | Voice-over / audio |
| --- | --- | --- |
| 0:00–0:20 | Saathi title; Sundarpur PHC and a simple case timeline. Keep the “Synthetic demo data” badge visible. | “This is Ramesh. His metformin refill is due, but the medicine is unavailable at his health centre. Saathi follows that gap until he receives the medicine.” |
| 0:20–0:48 | Patient role; open Hindi voice report. Play `s01.wav` with the label “Synthetic Gemini TTS voice.” Show recording/upload and the returned transcript. | “A patient or ASHA can describe the refill problem in Hindi.” **Hindi clip, 0:30–0:42:** “मेरी मेटफॉर्मिन की दवा खत्म हो गई… दवा नहीं मिली… घर में दो दिन की बची है।” Then: “The audio goes to Gemini for transcription and extraction.” |
| 0:48–1:10 | Editable transcript and extracted medicine, quantity, days remaining, and attempted date. Confirm to create the case. | “Ramesh reviews the words and fields before saving. Speech recognition can be wrong, so this confirmation is part of the flow.” |
| 1:10–1:35 | Pharmacist view; stock age, on-hand count, and verification action. Case status changes from reported to verified. | “A report is not yet a confirmed stockout. The pharmacist checks the shelf and records the result.” |
| 1:35–2:03 | District overview; point to separate prescription need, dispensing forecast, days left, and warning. | “The district sees the shortage beside medicine need and recent dispensing. The forecast is a planning signal, with known stockout days kept out of the dispensing series.” |
| 2:03–2:35 | Draft transfer from Nayagaon PHC; show donor, quantity, distance, safety and expiry checks, and AI source badge. Officer approves. | “The transfer engine finds an eligible donor and drafts a move. Gemini can explain the proposal, but the engine checks the stock constraints. A district officer decides whether to approve it.” |
| 2:35–3:04 | Dispatch and receipt actions; pharmacist supplies Ramesh. | “Staff dispatch the stock, the receiving centre records it, and the pharmacist supplies Ramesh. Each action is logged.” |
| 3:04–3:30 | Patient confirms receipt; case closes. End on the event history and concise synthetic-data notice. | “Ramesh confirms receipt, closing the loop. This is a synthetic prototype. Our simulation shows useful warning signals and real trade-offs; the next step is to test speech and the workflow with real users before field use.” |
