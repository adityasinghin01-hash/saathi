# Claude Design prompts — paste in order (one project, same chat)

## PROMPT 1 — Brand, logo, design system

You are a senior product designer at a top Indian design studio. Design the brand and design system for **[NAME]** (working name — suggest 3 better short bilingual names too), a public-health product for India.

WHAT IT DOES: It makes sure diabetes and blood-pressure patients at government health centres (PHCs) actually get their medicines. A patient (or village health worker, ASHA) reports a failed refill by voice → the PHC pharmacist verifies stock → the district officer sees medicine need vs stock with early warnings → an AI drafts a stock transfer from a nearby centre → the officer approves → medicine is dispatched, received, and handed to the patient → case closed.

USERS: (1) Patients, 40+, rural, low literacy, Hindi-first, cheap Android phones, often shared. (2) ASHA workers — village health workers, busy, outdoors. (3) PHC pharmacists — fast, repetitive work. (4) District health officers — desktop, data-dense decisions.

LANGUAGE: Fully bilingual **Hindi + English**, never Hindi-only. Every label shows both: Hindi primary + English secondary on patient/ASHA screens; English primary + Hindi secondary on pharmacist/district screens. Global toggle "हिं / EN" switches which is primary. Use one type family that covers both scripts properly: **IBM Plex Sans + IBM Plex Sans Devanagari** (tabular figures for all numbers). Check Devanagari line-height and matras never clip.

LOGO: Design a real logo — a simple symbol + wordmark in both Latin and Devanagari. Idea space: a medicine capsule that forms a closed loop / a bridge between two points (the loop closes when the patient gets the medicine). Must work in one colour, at 16 px favicon and 512 px app icon, and on dark/light. Show: primary lockup, stacked lockup, symbol only, app icon, clear-space and minimum-size rules. No generic cross, no heartbeat line, no stethoscope clichés.

VISUAL DIRECTION: Calm, trustworthy, precise — "a serious public service built by an excellent studio", not a startup landing page. References for the feel: GOV.UK Design System (clarity, plain language), Linear / Stripe dashboards (precision, density, alignment), Google Pay India (simplicity for first-time smartphone users). Warm paper-white background, deep ink text, ONE brand colour (choose it deliberately — not default blue, not purple). Status colours only carry meaning and are colour-blind safe with icons + text: red = out of stock / critical, amber = running low, green = resolved, grey = waiting.

SYSTEM TO DELIVER: colour tokens (with contrast ratios ≥ 4.5:1), type scale (mobile + desktop, both scripts), 8-pt spacing, 4-col mobile grid (360 px) and 12-col desktop grid (1440 px), radius and elevation (minimal), icon style (one consistent outline set, 1.5 px stroke), and components: buttons (primary/secondary/destructive, big 56 px touch targets on mobile), inputs, bilingual label pattern, status chips, case-timeline stepper, data-age badge ("updated 2 days ago"), stock bar, tables, cards, alert banners, offline banner ("saved offline — will send when online"), empty/loading/error states, "Synthetic demo data" badge, AI-draft badge ("Drafted by AI — needs your approval").

STRICTLY AVOID (AI look): gradients, glassmorphism, neon glows, emoji as icons, 3D blobs, stock photos, random illustrations, centred-everything hero layouts, lorem ipsum, more than one accent colour, rounded-everything cards floating on grey, fake testimonials.

Show the system as a clean spec sheet first. Wait for my feedback before screens.

---

## PROMPT 2 — Screens (send after the system is approved)

Using the approved design system and logo, design these screens. Real, realistic content (synthetic, labelled "Synthetic demo data"), perfect alignment to the grid, every screen bilingual.

PUBLIC
1. **Landing page (desktop + mobile)** — for judges and health officials. Sections: header with logo + "Open demo"; hero = the one-line promise + a crisp product visual (not a stock photo); the problem in 3 verified numbers (10.1 crore diabetes · 31.5 crore high BP · 8.64 crore under treatment in the national NCD programme); "How it works" 5-step loop diagram (Report → Verify → Forecast & warn → AI transfer draft → Close); the 4 roles; safety principles (no medical advice, every AI action needs human approval); footer.
2. **Login / role picker** — choose role (Patient, ASHA, Pharmacist, District officer) as large cards with icon + bilingual name; pick a demo user; language toggle; "Synthetic demo data" badge. Clean, centred card, not a marketing page.

PATIENT / ASHA (mobile, 360 px)
3. Home — my medicines, next refill date, big button "दवा नहीं मिली / Medicine not received".
4. Voice report — large mic button, live Hindi transcript, "speak or type" fallback.
5. Confirm — read-back of extracted fields (medicine, strength, centre, date tried, asked vs received, supply left at home) with edit pencil per field; confirm button.
6. My case — timeline stepper (Reported → Verified → Transfer → Received → Given to you → Closed) with dates.
7. Case closed — the demo climax: calm success state, "आपकी दवा मिल गई / You have your medicine".
8. ASHA: my patients list + report on behalf.

PHARMACIST (mobile + tablet)
9. Verify queue — list of reported cases with patient, medicine, waiting time.
10. Verify screen — stock on hand with data-age badge; 3 choices: Out of stock / Stock available / Household only.
11. Receive transfer + Give to patient (partial allowed).

DISTRICT OFFICER (desktop 1440 px)
12. Overview — left: map of PHCs coloured by worst status; right: dense table per PHC × medicine: on hand, data age, patients' refill need, dispensing forecast, days left, warning, open cases. Sortable, filter by block/medicine.
13. PHC × medicine detail — chart: patients' refill need vs dispensing forecast; stock-out periods shaded as "hidden demand"; days-left projection.
14. AI transfer draft review — proposed donor centre, quantity, batches + expiry, 3 constraint checks (donor keeps safety stock ✓, expiry ok ✓, units match ✓), AI rationale in plain language, Approve / Reject; also the "no transfer possible" variant.
15. Case board — columns by status; each card shows patient initials, medicine, PHC, age of case.
16. Audit trail drawer — every step with who and when.

STATES: for each main screen also show empty, loading, offline, error.

Output: a clickable prototype connecting the screens in the Ramesh story (Ramesh, 54, Meerut-like district, metformin 500 mg ran out → closed).
