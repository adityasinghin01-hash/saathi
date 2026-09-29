# Twelve hard judge questions — short answers

Use these as spoken answers. State the limit first when a question asks for evidence. The [claims ledger](02-NUMBERS-AND-CLAIMS.md) holds the exact numbers.

## 1. Isn't this HealthGrid AI again?

There is real overlap: the earlier Code for Communities HealthGrid team described voice stock updates, forecasts, district risk views and AI recommendations. [Their own account](https://www.linkedin.com/posts/saatvik-das_googlecloud-hack2skill-codeforcommunities-activity-7484472104856313856-2sh_) makes that clear, so we claim no first or exclusive idea. Our built demo concentrates on **one patient's refill case**: reported → pharmacist verified → constrained transfer → officer approval → centre receipt → patient handover → patient confirmation, with an audit trail. We have not run a controlled feature comparison or shown superior field performance.

## 2. Why build this if DVDMS and e-Aushadhi already exist?

They do exist. [PIB describes DVDMS](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2292469&lang=1&reg=1) as an IT platform for medicine procurement and availability, and the [UP CAG audit](https://cag.gov.in/uploads/download_audit_report/2024/H-CHAPTER-IV-Availability-of-drugs,-medicines,-Equipment-and-other-Consumables-067640dd62801a8.44640334.pdf) found limited sub-store module use at its test-checked facilities. Saathi's proposed role is to join stock information to patient refill need and track a verified case through delivery; DVDMS import/export is **NOT BUILT** and would need the authority's cooperation. We would integrate with an authoritative stock system rather than ask staff to maintain two permanent ledgers.

## 3. What proves this works on real data?

Nothing yet proves field impact. The people, prescriptions, stock and transfers in the app are synthetic. The forecast simulation generates patient need independently of the tested methods and includes breaking cases, but a supervised pilot must test real stock accuracy, alerts, staff time, patient receipt and missed medicine days. [Forecast report](../../backend/eval/results/forecast.md); [README](../../README.md#honest-evaluation).

## 4. Does the Hindi voice result generalise to patients?

No. In one paced API run, 12/12 scripted Hindi TTS clips got live Gemini answers with the scored fields matching their scripts; mean API latency was 5.96 seconds. The only tested human clip was a **non-refill** WhatsApp message, classified correctly on a standalone retry after an earlier fallback. Real refill voices, dialects, noisy clinics and varied phones are barely tested; the human review screen is therefore essential. [Audio report](../../backend/eval/results/audio.md).

## 5. What happens when AI invents a medicine or makes a bad transfer?

Missing voice fields remain null and block case creation until a person fills and confirms them. A pharmacist checks the shelf; OR-Tools applies donor reserve, matching drug/unit and expiry constraints; an officer must approve the draft. A provider failure shows a rules fallback, and no feasible donor returns an escalation instead of a fictional transfer. The text guard against advice is limited, so this is not clinical safety validation. [Contract](../CONTRACT.md#v06-29-sep-2026); [README](../../README.md#safety-and-data-limits).

## 6. Can every ASHA use a smartphone and this app?

We do not have a verified national ASHA smartphone-access rate. The prototype supports an ASHA reporting for an assigned patient and a patient typing instead of speaking. A pilot should select sites with suitable shared or existing devices, test usability and connectivity, and budget devices or assisted entry where needed. [PLAN §7](/Users/aditya/dev/c4c2-ideas/PLAN.md).

## 7. What about privacy, ABDM and patient consent?

Today's data are synthetic. The demo login is a public role picker, not secure identity, and we claim no ABDM integration or compliance. Before real records, a partner must set consent, identity, role access, retention, hosting, audit review and data-sharing rules; any ABDM/ABHA link needs partner access and the applicable programme process. [README](../../README.md#safety-and-data-limits); [PLAN §0.6](/Users/aditya/dev/c4c2-ideas/PLAN.md).

## 8. What will one district cost?

We have no verified ₹ per-district figure. The demo uses Vercel, Render and SQLite, which are not a priced district service. A pilot budget must count hosting, voice calls, devices, training, staff time, support, stock-system integration and security; we would publish actual cost per verified and closed case. [HANDOFF](../HANDOFF.md#live-29-sep-2026-10-am); [PLAN §13](/Users/aditya/dev/c4c2-ideas/PLAN.md).

## 9. Does it work offline?

Supported writes can be stored in an IndexedDB queue and replayed through `/api/v1/sync/batch` when the connection returns, with operation IDs to avoid duplicate application. Voice extraction, fresh district stock and transfer drafting still need connectivity. We need a field test for long outages, shared phones, conflict handling and whether staff can trust the stock timestamp. [README](../../README.md#what-the-prototype-does); [contract](../CONTRACT.md#v02-decisions-answers-to-codex-questions).

## 10. Who pays, and why would staff adopt another screen?

A state health mission or district programme is the proposed owner and payer, not a signed customer. The case must fit existing NCD and pharmacy work: one named stock custodian, one transfer authority, a response deadline and an import from the authoritative ledger. The pilot should measure added staff minutes and whether closing a case actually prevents an unsupported trip or missed refill. [PLAN §0.6 and §7](/Users/aditya/dev/c4c2-ideas/PLAN.md).

## 11. Won't prescription forecasts cause over-ordering?

Yes, that is a key result. In the baseline synthetic simulation, prescription-only reduced unmet patient-days from 227.58 to 3.33 versus dispensing-only, but had false alerts in one-third of runs and 389.19 mean overstock units. The shipped `max` rule is a separate product choice; neither method is validated on real demand. A pilot needs stale-prescription checks, reserve policies and explicit false-alert and overstock review before any ordering automation. [Forecast report](../../backend/eval/results/forecast.md); [contract default](../CONTRACT.md#v04-29-sep-2026).

## 12. Why not use WhatsApp and a spreadsheet?

That may be the right front door for some sites, and WhatsApp/IVR is on the roadmap. The hard part is the shared case state: who verified the shortage, which stock record is current, whether the donor can spare the right batch, who approved, and whether the patient received it. Saathi demonstrates those gates and audit events in one synthetic workflow. A pilot should compare it with the site's existing messaging and ledger routine; no efficiency gain is claimed yet. [PLAN §0.4–§0.6](/Users/aditya/dev/c4c2-ideas/PLAN.md); [contract](../CONTRACT.md#case-status-machine).
