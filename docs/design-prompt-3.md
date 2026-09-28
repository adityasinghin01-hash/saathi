Continue the Saathi · साथी product design in THIS project, on the same canvas, using the same Saathi design system, the same files (saathi.css, bundle.css, app.css), the same icon sprite, the same bilingual .sa-bi pattern and the same हिं/EN toggle as the 21 boards already here. Reuse the existing shells exactly (M-Shell-Patient topbar + tabbar, M-Shell-Pharmacist, W-Shell sidebar + topbar). Do not redesign anything that exists.

FIRST — fix the demo names on ALL boards (existing and new). The demo data is fictional and must match our backend:
- District: Suryanagar (सूर्यनगर). Never Meerut or any real place.
- Centres: Sundarpur PHC (Ramesh's centre, out of Metformin), Nayagaon PHC (the donor), Amarpur PHC, Shantipur PHC, Navgram PHC, Udaypur PHC, Suryanagar District Store. Six PHCs + one store, not 42 centres.
- Medicines: Metformin 500 mg, Glimepiride 1 mg, Amlodipine 5 mg, Telmisartan 40 mg. Nothing else.
- People: Ramesh (patient, 54), ASHA Rekha, Pharmacist Sunita, District officer Dr. Mehra.
- Every screen keeps the "SYNTHETIC DEMO DATA / नमूना डेटा" badge.

THEN design these 18 boards. Phone = 360 px (Hindi leads), web = 1440 px (English leads). Name files M-… and W-… like the existing ones, add them to the canvas in new titled sections, and link them into one clickable Ramesh flow.

6 · Patient + ASHA — phone
6.1 M-Voice — "दवा नहीं मिली" tapped: huge mic button, recording state with live Hindi transcript appearing, "type instead" fallback, cancel.
6.2 M-Confirm — read-back of what we understood: medicine, strength, centre, date tried, quantity asked vs received, tablets left at home. Edit pencil per field. Big "सही है / Confirm". Small note: "यह रिपोर्ट है, अभी पुष्टि नहीं / Reported — not yet confirmed by the pharmacist".
6.3 M-Case — Ramesh's case: timeline stepper Reported → Verified by pharmacist → Transfer on the way → Arrived at centre → Given to you → Closed, with dates/times; current step highlighted; what happens next in one plain line.
6.4 M-Closed — calm success: "आपकी दवा मिल गई / You have your medicine", what was given, confirm-received button, no confetti.
6.5 M-Asha-Home — ASHA Rekha's home: list of her patients with next-refill status chips (out / low / ok / waiting), "report for a patient" button.
6.6 M-Asha-Report — pick patient → then reuses the voice flow (show the pick step + a "reporting for Ramesh" header on the voice screen).

7 · Pharmacist — phone
7.1 M-Verify — one reported case: patient, medicine, what they said (transcript), stock on hand with a data-age badge ("updated 2 h ago"), three big choices: Out of stock / Stock is available / Patient still has some at home. Entering on-hand count.
7.2 M-Receive-Give — incoming transfer from Nayagaon PHC: quantity, batch + expiry, "mark received"; then "give to patient" with quantity (partial allowed, shows given / asked).
7.3 M-Stock — update today's stock count for the 4 medicines, last-updated age per row, save (works offline: show the "saved offline — will send when online" banner).

8 · District officer — web
8.1 W-Overview — the working table (not the welcome dashboard): rows = PHC × medicine; columns: on hand, data age, patients' need (from prescriptions), dispensing forecast, days left, warning chip, open cases. Sortable headers, filters for centre and medicine. A small map/list of the 6 PHCs coloured by worst status on the left.
8.2 W-Facility — Sundarpur PHC × Metformin detail: chart of patients' need vs dispensing forecast vs stock over 60 days, stock-out days shaded and labelled "hidden demand — patients came, no medicine", days-left projection, open cases list, "Draft a transfer" button.
8.3 W-Transfer-Draft — AI transfer draft review: donor Nayagaon PHC → Sundarpur PHC, quantity, batches + expiry, three checks with ticks (donor keeps its safety stock · no batch expires before use · units match), the AI's reason in 2 plain sentences, badge "Drafted by AI — needs your approval". Buttons Approve / Reject (reject asks for a note). Also show two variants on the same board: (a) "No safe transfer possible — escalate to district store", (b) AI unavailable: badge "Drafted by rules — AI was unavailable".
8.4 W-Transfers — list of transfers by state (Drafted, Approved, Dispatched, Received) with a Dispatch button on approved ones.
8.5 W-Cases — case board, columns by status (Reported, Verified, Transfer, Received, Supplied, Closed); card = patient initials, medicine, PHC, age of case.
8.6 W-Audit — audit trail drawer over W-Cases: every step of Ramesh's case with who, role, and time.
8.7 W-Evaluation — "How well does the warning work?": our honest test on synthetic data. Show two numbers big: patient-days without medicine 228 → 3 (−99%) and the cost: it over-orders (a false alarm in 1 of every 3 test runs, and extra stock sitting on the shelf). One plain-language line each. Label "Synthetic simulation — not real patients".

9 · States
9.1 M-States — one board with empty, loading, offline, error for a phone screen.
9.2 W-States — same four for the web table.

RULES (never break): the app never gives medical advice and never shows sugar/BP/HbA1c numbers · every AI action needs a human Approve · a shortage is "reported" until the pharmacist confirms it · status colour always comes with an icon + text · real, specific content, no lorem ipsum · keep Devanagari matras from clipping.

WHEN DONE: save/publish the project so all boards are in the shared artifact link, and list every board title in your reply.
