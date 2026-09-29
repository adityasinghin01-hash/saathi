# Saathi · साथी — 12-slide build brief

**For the deck builder:** Make exactly 12 slides. Each English headline below is at most ten words; put its Hindi subtitle directly below it. Pair Hindi and English on other visible labels too. Keep **Synthetic demo data** visible on every screenshot and beside every prototype or evaluation result. Put **BUILT PROTOTYPE** on current screens and **NOT BUILT — ROADMAP** on future features. Use the linked ledger in [02-NUMBERS-AND-CLAIMS.md](02-NUMBERS-AND-CLAIMS.md) for every figure. Place short source footnotes on slides 2 and 7; put full citations in notes. Do not crop away qualifiers or turn simulator results into patient outcomes.

**Plain-word key:** PHC = primary health centre; ASHA = community health worker; TSB = a method for forecasting uneven dispensing; “unmet patient-days” = the simulator's count of patients spending a day without the requested medicine.

## 1. Saathi closes the refill loop

**Hindi subtitle:** साथी: दवा मिलने तक मामला खुला रहे

**On-slide lines**
- **Saathi · साथी**
- A missed PHC refill becomes a case that stays visible until medicine reaches the patient.
- Patient/ASHA → pharmacist → district officer → patient confirmation.
- **BUILT PROTOTYPE · Synthetic demo data**

**Visual:** S01 landing hero and logo. Keep the title large; the loop can be one thin line.

**Speaker notes:** Saathi is a synthetic demonstration for Code for Communities, second edition, Track 3. The demo focuses on Ramesh's metformin refill and follows it to confirmation; it is not clinical or production inventory software. Source: [README](../../README.md), [description](../description-final.md).

**Judging:** Problem fit; Impact.

## 2. Medicine demand is large; supply gaps are real

**Hindi subtitle:** दवा की ज़रूरत बड़ी है; आपूर्ति में कमी है

**On-slide lines**
- **10.1 crore** people with diabetes and **31.5 crore** with hypertension: India, 2021 estimates.
- A UP audit found that at some test-checked PHCs, **up to 16 of 20 sampled drugs** were never available in 2018–22.
- These are disease burden and audited facility findings, **not Saathi's impact**.
- A missed chronic refill needs a visible owner and follow-through.

**Visual:** Two large sourced numbers and a small S08 shelf/stock screen crop. Footnotes: ICMR-INDIAB-17 (2023); CAG UP Report No. 8 of 2024, chapter IV. Keep “some test-checked PHCs” attached to 16/20.

**Speaker notes:** The ICMR-INDIAB figures are projected counts for 2021 and should not be added because one person can have both conditions. The CAG finding is a maximum among sampled PHCs, not a state or national shortage rate. Saathi addresses the operational gap shown by these sources, but no field outcome has been measured. Sources: [ICMR-INDIAB-17](https://doi.org/10.1016/S2213-8587(23)00119-5), [CAG UP chapter IV](https://cag.gov.in/uploads/download_audit_report/2024/H-CHAPTER-IV-Availability-of-drugs,-medicines,-Equipment-and-other-Consumables-067640dd62801a8.44640334.pdf).

**Judging:** Problem fit; Impact.

## 3. Empty shelves can hide demand

**Hindi subtitle:** खाली शेल्फ़ असली ज़रूरत छिपाती है

**On-slide lines**
- When a medicine is out of stock, **dispensing can read zero even while patients still need it**.
- Saathi shows staff-confirmed prescription need beside a separate dispensing forecast.
- Known stockout days are excluded from the dispensing series; the two estimates are **not added**.
- Stock age and a patient's reported shortage add context; staff must verify the report.

**Visual:** D4-HIDDEN-DEMAND, with S12 as a small interface example if space allows.

**Speaker notes:** This is the censored-demand problem: dispensing records measure what was supplied, not everything requested. The current product uses the larger of cohort need and dispensing forecast for enrolled-dominant demo drugs, and the district view marks stock age. The forecast experiment is synthetic and has trade-offs shown on slide 7. Sources: [contract](../CONTRACT.md#forecast-rules-district), [README](../../README.md#what-the-prototype-does), [forecast report](../../backend/eval/results/forecast.md).

**Judging:** Tech/AI; Problem fit.

## 4. One case, four roles, five steps

**Hindi subtitle:** एक मामला, चार भूमिकाएँ, पाँच कदम

**On-slide lines**
- Ramesh or Rekha reports a failed refill in Hindi or by form.
- Sunita verifies the shelf before the report becomes a confirmed stockout.
- The district sees need, stock, and a checked transfer draft; Dr. Mehra approves.
- Staff dispatch, receive, and hand over; Ramesh confirms receipt to close.

**Visual:** D1-REFILL-LOOP. Use four role colours and one case line; caption **BUILT PROTOTYPE · Synthetic demo data**.

**Speaker notes:** Ramesh, Rekha, Sunita and Dr. Mehra are synthetic demo users. The case can instead be marked stock available, household-only, cancelled, or left verified when no transfer is feasible. The diagram shows the main Ramesh path, not an automatic medicine delivery. Sources: [contract](../CONTRACT.md#case-status-machine), [README](../../README.md#what-the-prototype-does).

**Judging:** Problem fit; Deployability; Impact.

## 5. Watch Ramesh's case reach closed

**Hindi subtitle:** रमेश का मामला पूरा होने तक

**On-slide lines**
- **Reported:** Rekha checks the Hindi transcript and fields before sending.
- **Verified:** Sunita enters the on-hand count at Sundarpur PHC.
- **Draft → approved → dispatched → received:** Nayagaon is the eligible donor in this seed.
- **Supplied → closed:** Sunita hands over; Ramesh confirms; the audit trail records each step.

**Visual:** D5-RAMESH-SEQUENCE plus S23 → S09 → S13 → S17, or four crops with S18 as the ending inset. S23 shows a Hindi transcript in an English UI; do not call the whole screen Hindi-first.

**Speaker notes:** Keep one case ID through the sequence; the screenshots are a synthetic run. The transfer engine checks donor reserve, matching medicine and unit, and batch expiry before a draft appears. Receiving medicine at a centre is distinct from handing it to the patient and closing the case. Sources: [video shot list](../video-shotlist.md), [contract](../CONTRACT.md#case-status-machine), [seed notes](../notes-codex.md#round-8-seed-realism-follow-up-29-sep-2026).

**Judging:** Deployability; Impact.

## 6. AI drafts; people make the decisions

**Hindi subtitle:** एआई मसौदा बनाता है; निर्णय लोग लेते हैं

**On-slide lines**
- Gemini extracts voice fields; the patient or ASHA reads and corrects them.
- TSB and prescription need help the district see risk; a pharmacist verifies actual stock.
- OR-Tools checks eligible donors; Gemini may explain the checked draft.
- An officer approves, staff move stock, and the patient confirms receipt.
- AI gives **no treatment advice** and cannot approve a transfer.

**Visual:** D3-AI-AND-HUMAN-GATES, supported by S06 and S13 crops.

**Speaker notes:** Voice extraction alone does not create a case, and a non-refill statement should not become one. Gemini's transfer role is a bounded explanation of engine-checked facts; provider failure shows a rules fallback badge. This is decision support with human gates, not a free-acting clinical agent. Sources: [contract](../CONTRACT.md#v06-29-sep-2026), [README](../../README.md#safety-and-data-limits).

**Judging:** Tech/AI; Deployability.

## 7. The forecast helps, with a cost

**Hindi subtitle:** अनुमान मदद करता है, पर उसकी कीमत है

**On-slide lines**
- **Synthetic simulation, baseline:** dispensing-only had **227.58** unmet patient-days per run.
- Prescription-only cut that to **3.33**, but had **1-in-3 false alerts** and **389.19 mean overstock units**.
- Experimental combined had lower error (**3.81 vs 4.98 units/day**) but **the same 227.58 unmet patient-days**.
- **Shipped default:** the separate `max` rule; no field benefit has been measured.

**Visual:** D4-HIDDEN-DEMAND, evaluation half, plus S19 if legible. Label each method and the synthetic simulator. Do not imply 228→3 is the shipped system's outcome.

**Speaker notes:** The 228→3 shorthand compares dispensing-only with prescription-only in the baseline simulation, not Saathi before and after deployment. The experimental combined method reduced average absolute error but did not reduce baseline unmet patient-days; under stale prescriptions, its error and overstock rose sharply. The field pilot must test forecast accuracy, false alarms, stockout days, and actual patient receipt. Sources: [forecast report](../../backend/eval/results/forecast.md), [contract default](../CONTRACT.md#v04-29-sep-2026).

**Judging:** Tech/AI; Impact.

## 8. A deployable prototype with clear limits

**Hindi subtitle:** चलने वाला नमूना, स्पष्ट सीमाएँ

**On-slide lines**
- Phone/web PWA on **Vercel Next.js**; **Render FastAPI** with a **SQLite demo** store.
- TSB forecast, OR-Tools transfer checks, Gemini voice/rationale with rules fallback.
- Supported offline writes queue in IndexedDB and replay through `/api/v1/sync/batch`.
- Case events form an audit trail; stock numbers show when they were recorded.
- **Live demo:** https://saathi-drab.vercel.app

**Visual:** D2-ARCHITECTURE plus S10 district view. Caption SQLite, demo role picker and browser queue as prototype choices.

**Speaker notes:** The public demo uses Vercel and Render; the Render free service may wake slowly after idle. The offline queue covers supported writes and sends them later; it does not make live stock or voice available without connectivity. The demo role picker has no secure authentication, and SQLite needs replacement or hardening before a field rollout. Sources: [README](../../README.md), [handoff live section](../HANDOFF.md#live-29-sep-2026-10-am), [contract](../CONTRACT.md#api-prefix-apiv1).

**Judging:** Deployability; Tech/AI.

## 9. Trust starts with visible boundaries

**Hindi subtitle:** भरोसे के लिए स्पष्ट सीमाएँ

**On-slide lines**
- A patient report stays **reported** until a pharmacist checks stock.
- Missing voice fields stay blank; a person confirms before a case is saved.
- Transfer checks protect donor reserve, units, and expiry; the officer approves.
- No generated treatment advice or invented glucose number; every case transition is logged.
- All shown patients and stock are **Synthetic demo data**.

**Visual:** S06 review, S13 approval checks, S18 audit trail as three readable crops.

**Speaker notes:** The text screen for advice and invented sugar numbers is limited; it is not a clinical safety classifier. If no donor qualifies, the system returns no feasible transfer and leaves the case for escalation. Real deployment also needs consent, secure identity, privacy controls, and named stock and transfer authorities. Sources: [README](../../README.md#safety-and-data-limits), [contract](../CONTRACT.md#transfer-engine-rules).

**Judging:** Deployability; Impact.

## 10. Scale only after a measured pilot

**Hindi subtitle:** मापे हुए पायलट के बाद ही विस्तार

**On-slide lines**
- **Prototype now:** one synthetic district and a complete refill case loop.
- **Proposed pilot:** one block, about 5–6 PHCs; named stock custodian and transfer authority.
- Compare stockout days, patients without medicine, private spending, and alert lead time.
- State rollout needs authoritative stock data, consent, identity, training, and support.
- National integrations require proven state workflows and partner access.

**Visual:** D6-SCALE-AND-ROADMAP. Mark every step beyond prototype **NOT BUILT**.

**Speaker notes:** The one-block size is a plan, not a signed pilot or coverage achieved. State health missions or district programmes would need to own adoption and pay for hosting, support, and staff time; no per-district cost has been verified. The later national rails are interoperability targets, subject to partner access and approval. Sources: [PLAN §0.6 and §7](/Users/aditya/dev/c4c2-ideas/PLAN.md), [README roadmap](../../README.md#roadmap).

**Judging:** Scale across India; Deployability; Impact.

## 11. Full system roadmap — NOT BUILT

**Hindi subtitle:** पूरी प्रणाली की आगे की योजना — अभी नहीं बनी

**On-slide lines**
- **Care view:** doctor QR summary, finger-prick glucose diary, meal/photo and personal glucose research.
- **Community work:** ASHA task/agent tab, callback and WhatsApp/IVR after field testing.
- **Supply data:** stock-register photo reading, DVDMS import/export, wider transfer workflows.
- **Shared learning:** federated demand research; NCD portal and ABDM/ABHA integration only with partners.
- **Research gates:** clinician review, held-out baselines; MedGemma/PaliGemma and quantum tests only if useful.

**Visual:** D6 roadmap lane. Put a large **NOT BUILT — ROADMAP / RESEARCH** band across this slide; do not place prototype screenshots behind roadmap claims.

**Speaker notes:** The full PLAN covers patient, ASHA, doctor, district and state-facing work, but the current prototype implements only the refill-resolution loop. The older plan's broad demo-scope rows were targets, not evidence that these modules shipped. Attendance signals and screening add-ons are also unbuilt ideas; none should be described as deployed or clinically validated. Source: [PLAN §0.4–§10](/Users/aditya/dev/c4c2-ideas/PLAN.md), [README roadmap](../../README.md#roadmap).

**Judging:** Scale across India; Tech/AI.

## 12. Test the loop with real teams

**Hindi subtitle:** असली टीमों के साथ प्रक्रिया जाँचें

**On-slide lines**
- **Ask:** a supervised pilot with real stock records and consenting users.
- Measure whether cases close with medicine in hand, and at what staff cost.
- **Team:** Aditya; add the official team name and other members from the submission form before export.
- **Try:** https://saathi-drab.vercel.app · **Code:** github.com/adityasinghin01-hash/saathi
- **API:** https://saathi-api-gm4i.onrender.com · **Synthetic demo data**

**Visual:** S17 closed case and Saathi logo. Add QR codes only after checking the URLs in the final exported deck.

**Speaker notes:** The repo is private in the current handoff, so a judge may need access or a public release before the code link works. Do not invent teammates or institutional affiliations; fill those fields from the official entry. This is an invitation to test the workflow and its limits, not a claim of measured health impact. Sources: [handoff](../HANDOFF.md#live-29-sep-2026-10-am), [README](../../README.md).

**Judging:** Impact; Deployability; Scale across India.
