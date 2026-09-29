"""Six Saathi diagram specs. Run run_all.py only where Chrome can render PDFs.

Each diagram's Mermaid drawing and redraw specification share the same nodes and
arrows. All patient, stock, transfer and evaluation figures are synthetic.
"""
import html
import os
import subprocess

OUT = "/Users/aditya/dev/refill-loop/docs/ppt-pack"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# ---------------------------------------------------------------- helpers
def mm_label(t):
    return t.replace('"', "'").replace("\n", "<br/>")

def flowchart(direction, groups, edges, core=(), dashed=(), classes=None):
    """groups: (group_id, group_title, [(node_id, label), ...] or nested groups).
    edges: (source_id, destination_id, label).
    """
    lines = [f"flowchart {direction}"]
    def emit(g, ind="  "):
        gid, title, items = g
        lines.append(f'{ind}subgraph {gid}["{mm_label(title)}"]')
        for it in items:
            if len(it) == 3 and isinstance(it[2], list):
                emit(it, ind + "  ")
            else:
                nid, lab = it
                lines.append(f'{ind}  {nid}["{mm_label(lab)}"]')
        lines.append(f"{ind}end")
    for g in groups:
        emit(g)
    for a, b, lab in edges:
        arrow = "-.->" if (a, b) in dashed else "-->"
        lines.append(f'  {a} {arrow}|"{mm_label(lab)}"| {b}' if lab else f"  {a} {arrow} {b}")
    if core:
        lines.append("  classDef core fill:#fdefd3,stroke:#b04a24,stroke-width:2px")
        lines.append("  class " + ",".join(core) + " core")
    if classes:
        for cname, style, ids in classes:
            lines.append(f"  classDef {cname} {style}")
            lines.append(f"  class {','.join(ids)} {cname}")
    return "\n".join(lines)

def spec(groups, edges):
    names = {}
    out = ["BOXES (grouped exactly as drawn):"]
    def walk(g, depth=0):
        gid, title, items = g
        out.append("  " * depth + f"■ {title.replace(chr(10), ' ')}")
        for it in items:
            if len(it) == 3 and isinstance(it[2], list):
                walk(it, depth + 1)
            else:
                nid, lab = it
                names[nid] = lab.replace("\n", " ")
                out.append("  " * (depth + 1) + f"- [{nid}] {names[nid]}")
    for g in groups:
        walk(g)
    out.append("")
    out.append(f"CONNECTIONS ({len(edges)} arrows, from → to : what flows):")
    for a, b, lab in edges:
        out.append(f"  {names.get(a, a)}  →  {names.get(b, b)}" + (f"   : {lab.replace(chr(10), ' ')}" if lab else ""))
    return "\n".join(out)

def page(fname, title, subtitle, mermaid_code, spec_text, extra_html="", size="A2 landscape"):
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
@page {{ size: {size}; margin: 12mm; }}
body {{ font-family: 'IBM Plex Sans', 'IBM Plex Sans Devanagari', Arial, sans-serif; color:#2e2119; background:#fbf4ea; }}
h1 {{ font-size: 26px; margin: 0 0 4px; }} .sub {{ color:#6a5444; margin-bottom: 10px; font-size: 14px; }}
.mermaid {{ text-align:center; }}
h2 {{ font-size: 18px; border-bottom: 2px solid #bf5630; margin-top: 18px; page-break-before: always; }}
pre.spec, pre.code {{ font-size: 11.5px; white-space: pre-wrap; background:#fffaf3; padding:10px; border:1px solid #e8d9c6; }}
.note {{ font-size: 12px; color:#6a5444; }}
</style></head><body>
<h1>{html.escape(title)}</h1><div class="sub">{html.escape(subtitle)}</div>
<pre class="mermaid">{html.escape(mermaid_code)}</pre>
{extra_html}
<h2>Exact spec for redrawing</h2>
<p class="note">Keep every box, group and arrow below. Keep BUILT and NOT BUILT labels. Styling may change; meaning must not.</p>
<pre class="spec">{html.escape(spec_text)}</pre>
<h2>Mermaid source</h2>
<pre class="code">{html.escape(mermaid_code)}</pre>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true, theme:'default', flowchart:{{useMaxWidth:true, htmlLabels:true, curve:'basis'}}}});</script>
</body></html>"""
    hp = os.path.join(OUT, "_build", fname + ".html")
    with open(hp, "w", encoding="utf-8") as handle:
        handle.write(doc)
    pdf = os.path.join(OUT, fname + ".pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=30000", f"--print-to-pdf={pdf}", hp],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print("wrote", pdf)

# D1 · Five stages across four roles. The arrows describe the main synthetic Ramesh case.
D1_groups = [
    ("S1", "1 · Report / रिपोर्ट · Ramesh or Rekha / रमेश या रेखा", [
        ("d1_voice", "Ramesh or ASHA Rekha reports a failed metformin refill\nरमेश या आशा रेखा दवा न मिलने की रिपोर्ट करते हैं"),
        ("d1_read", "Human checks voice fields or uses the form\nव्यक्ति सुनकर जाँचता है या फ़ॉर्म भरता है"),
    ]),
    ("S2", "2 · Verify / पुष्टि · Sunita / सुनीता", [
        ("d1_verify", "Pharmacist checks timestamped stock\nफ़ार्मासिस्ट समय सहित स्टॉक जाँचती है"),
    ]),
    ("S3", "3 · Plan and approve / योजना और मंज़ूरी · Dr. Mehra / डॉ. मेहरा", [
        ("d1_need", "District sees prescription need, dispensing forecast and stock age\nज़िला ज़रूरत, वितरण अनुमान और डेटा की उम्र देखता है"),
        ("d1_draft", "Eligible transfer drafted; officer approves or rejects\nयोग्य ट्रांसफ़र का मसौदा; अधिकारी मंज़ूर या रद्द करते हैं"),
    ]),
    ("S4", "4 · Move and hand over / पहुँचाना · Officer and Sunita / अधिकारी और सुनीता", [
        ("d1_move", "Officer dispatches; pharmacist receives and hands over\nअधिकारी भेजते हैं; फ़ार्मासिस्ट लेकर रोगी को देती है"),
    ]),
    ("S5", "5 · Confirm / पुष्टि · Ramesh / रमेश", [
        ("d1_close", "Ramesh confirms receipt; case closes with audit events\nरमेश प्राप्ति की पुष्टि करते हैं; मामला बंद होता है"),
    ]),
]
D1_edges = [
    ("d1_voice", "d1_read", "editable / सुधार सकते हैं"),
    ("d1_read", "d1_verify", "reported / रिपोर्ट दर्ज"),
    ("d1_verify", "d1_need", "verified stockout / स्टॉक खत्म होने की पुष्टि"),
    ("d1_need", "d1_draft", "risk and case / चेतावनी और मामला"),
    ("d1_draft", "d1_move", "approved transfer / मंज़ूर ट्रांसफ़र"),
    ("d1_move", "d1_close", "supplied / दवा दी गई"),
]
D1_classes = [("human", "fill:#e6eedc,stroke:#6d8a5a,stroke-width:2px", ["d1_read", "d1_verify", "d1_draft", "d1_move", "d1_close"])]

# D2 · Current deployed architecture. The browser queues only supported writes.
D2_groups = [
    ("CLIENT", "Phone or web / फ़ोन या वेब · BUILT PROTOTYPE", [
        ("d2_pwa", "Bilingual PWA screens / द्विभाषी ऐप स्क्रीन"),
        ("d2_queue", "IndexedDB offline queue for supported writes\nसमर्थित काम ऑफ़लाइन कतार में"),
    ]),
    ("HOST", "Hosting / होस्टिंग", [
        ("d2_next", "Vercel · Next.js frontend / फ़्रंटएंड"),
        ("d2_api", "Render · FastAPI / एपीआई"),
    ]),
    ("SERVICE", "FastAPI services / सेवाएँ", [
        ("d2_forecast", "Prescription need + TSB dispensing forecast\nपर्चे की ज़रूरत + वितरण अनुमान"),
        ("d2_transfer", "OR-Tools donor and batch checks\nदाता और बैच की जाँच"),
        ("d2_gemini", "Gemini voice extraction and checked rationale\nआवाज़ से विवरण और जाँचा हुआ कारण"),
        ("d2_fallback", "Rules fallback when Gemini unavailable\nएआई न चले तो नियम आधारित मसौदा"),
        ("d2_audit", "Case events and audit log / मामले का पूरा रिकॉर्ड"),
    ]),
    ("STORE", "Demo store / नमूना डेटा", [
        ("d2_sqlite", "SQLite · synthetic patients, stock, cases, transfers\nनमूना रोगी, स्टॉक, मामले और ट्रांसफ़र"),
    ]),
]
D2_edges = [
    ("d2_pwa", "d2_next", "web app / वेब ऐप"),
    ("d2_next", "d2_api", "HTTPS API / एपीआई"),
    ("d2_api", "d2_sqlite", "case and stock reads/writes / मामला और स्टॉक डेटा"),
    ("d2_pwa", "d2_queue", "offline supported write / ऑफ़लाइन काम"),
    ("d2_queue", "d2_api", "later /api/v1/sync/batch"),
    ("d2_api", "d2_forecast", "district view / ज़िला दृश्य"),
    ("d2_api", "d2_transfer", "draft request / मसौदा अनुरोध"),
    ("d2_api", "d2_gemini", "voice or rationale / आवाज़ या कारण"),
    ("d2_gemini", "d2_fallback", "provider failure / एआई विफल"),
    ("d2_api", "d2_audit", "status change / स्थिति बदली"),
    ("d2_forecast", "d2_sqlite", "read history / इतिहास पढ़े"),
    ("d2_transfer", "d2_sqlite", "read stock and batches / स्टॉक पढ़े"),
    ("d2_audit", "d2_sqlite", "append events / रिकॉर्ड लिखे"),
]
D2_dashed = {("d2_gemini", "d2_fallback")}
D2_classes = [("data", "fill:#fdefd3,stroke:#b57a10,stroke-width:2px", ["d2_sqlite"])]

# D3 · Models and algorithms advise; named people take the actual actions.
D3_groups = [
    ("INPUT", "Input and AI / जानकारी और एआई · BUILT", [
        ("d3_voice", "Gemini extracts transcript and nullable refill fields\nएआई सुनी बात और कही गई जानकारी लिखता है"),
        ("d3_review", "Patient or ASHA corrects and confirms before case save\nरोगी या आशा सुधारकर भेजते हैं"),
    ]),
    ("STOCK", "Stock and planning / स्टॉक और योजना · BUILT", [
        ("d3_pharm", "Pharmacist checks shelf and enters on-hand stock\nफ़ार्मासिस्ट स्टॉक की पुष्टि करती है"),
        ("d3_forecast", "Prescription need + TSB warning are planning signals\nपर्चे की ज़रूरत और अनुमान केवल संकेत हैं"),
        ("d3_engine", "OR-Tools checks same drug/unit, donor reserve and expiry\nनियम से दाता, सुरक्षित स्टॉक और तारीख जाँचें"),
        ("d3_reason", "Gemini words checked rationale; rules fallback if unavailable\nएआई जाँचा कारण लिखता है; ज़रूरत पर नियम आधारित जवाब"),
    ]),
    ("ACTION", "People act / लोग निर्णय लेते हैं · BUILT", [
        ("d3_officer", "District officer approves or rejects transfer\nज़िला अधिकारी मंज़ूरी या अस्वीकृति देते हैं"),
        ("d3_dispatch", "Officer dispatches; pharmacist records receipt and handover\nअधिकारी भेजते हैं; फ़ार्मासिस्ट लेकर दवा देती है"),
        ("d3_patient", "Patient confirms receipt; case closes\nरोगी प्राप्ति की पुष्टि करता है"),
    ]),
    ("NEVER", "AI never / एआई कभी नहीं", [
        ("d3_never", "No treatment advice, diagnosis, invented glucose number,\nautomatic transfer approval or patient confirmation\nइलाज सलाह, अनुमानित शुगर या अपने-आप मंज़ूरी नहीं"),
    ]),
]
D3_edges = [
    ("d3_voice", "d3_review", "draft only / केवल मसौदा"),
    ("d3_review", "d3_pharm", "reported case / रिपोर्ट दर्ज"),
    ("d3_pharm", "d3_forecast", "verified stock / पक्का स्टॉक"),
    ("d3_forecast", "d3_engine", "need and available stock / ज़रूरत और स्टॉक"),
    ("d3_engine", "d3_reason", "checked donor facts / जाँचे तथ्य"),
    ("d3_reason", "d3_officer", "draft for review / मंज़ूरी के लिए"),
    ("d3_officer", "d3_dispatch", "approved / मंज़ूर"),
    ("d3_dispatch", "d3_patient", "supplied / दवा दी गई"),
]
D3_classes = [
    ("gate", "fill:#e6eedc,stroke:#6d8a5a,stroke-width:2px", ["d3_review", "d3_pharm", "d3_officer", "d3_dispatch", "d3_patient"]),
    ("prohibit", "fill:#fbe4df,stroke:#a3231b,stroke-width:2px", ["d3_never"]),
]

# D4 · Distinguish the phenomenon, shipped signal, and the independent simulation.
D4_groups = [
    ("CAUSE", "Hidden need / छिपी ज़रूरत", [
        ("d4_need", "Patients still need refills / रोगियों को दवा चाहिए"),
        ("d4_empty", "PHC shelf runs out / केंद्र में दवा खत्म"),
        ("d4_zero", "Dispensing can read zero / वितरण शून्य दिख सकता है"),
        ("d4_bias", "Dispensing alone can undercount need\nकेवल वितरण से ज़रूरत कम दिख सकती है"),
    ]),
    ("BUILT", "Current product / अभी बना", [
        ("d4_rx", "Staff-confirmed prescriptions give cohort need\nपुष्ट पर्चों से रोगियों की ज़रूरत"),
        ("d4_tsb", "TSB on dispensing; exclude known stockout days\nवितरण अनुमान में स्टॉक खत्म दिन हटें"),
        ("d4_max", "Show both; demo default = larger value, never sum\nदोनों अलग दिखें; बड़ा मान लें, जोड़ें नहीं"),
    ]),
    ("EVAL", "Synthetic simulation / नमूना प्रयोग · NOT field impact", [
        ("d4_base", "Dispensing-only: 227.58 unmet patient-days/run\nकेवल वितरण: 227.58"),
        ("d4_rxonly", "Prescription-only: 3.33 unmet; 1-in-3 false alerts;\n389.19 mean overstock units / अधिक स्टॉक"),
        ("d4_comb", "Experimental combined: MAE 3.81 vs 4.98 units/day;\nboth 227.58 unmet / लाभ समान"),
    ]),
]
D4_edges = [
    ("d4_need", "d4_empty", "need persists / ज़रूरत बनी रहती है"),
    ("d4_empty", "d4_zero", "supply stops / दवा नहीं मिली"),
    ("d4_zero", "d4_bias", "censored record / अधूरा रिकॉर्ड"),
    ("d4_rx", "d4_max", "cohort need / पर्चे की ज़रूरत"),
    ("d4_tsb", "d4_max", "dispensing estimate / वितरण अनुमान"),
    ("d4_base", "d4_rxonly", "method comparison / तरीकों की तुलना"),
    ("d4_base", "d4_comb", "method comparison / तरीकों की तुलना"),
]
D4_classes = [("sim", "fill:#fdefd3,stroke:#b57a10,stroke-width:2px", ["d4_base", "d4_rxonly", "d4_comb"])]

# D5 · The exact main-path case statuses, with transfer approval and centre receipt distinct.
D5_groups = [
    ("PAT", "Patient or ASHA / रोगी या आशा", [
        ("d5_report", "Ramesh or Rekha: voice/form → read-back → reported\nरमेश या रेखा: जाँचकर रिपोर्ट दर्ज"),
    ]),
    ("PHA", "Pharmacist Sunita / फ़ार्मासिस्ट सुनीता", [
        ("d5_verify", "Sundarpur stock checked → verified\nसुंदरपुर स्टॉक जाँचा → पुष्टि"),
    ]),
    ("OFF", "District officer Dr. Mehra / ज़िला अधिकारी डॉ. मेहरा", [
        ("d5_draft", "Nayagaon eligible → transfer_drafted\nनयागाँव योग्य → ट्रांसफ़र मसौदा"),
        ("d5_approve", "Officer approves → transfer_approved\nअधिकारी मंज़ूर करते हैं"),
        ("d5_dispatch", "Officer dispatches → dispatched\nअधिकारी दवा भेजते हैं"),
    ]),
    ("RETURN", "Centre then patient / केंद्र फिर रोगी", [
        ("d5_receive", "Sunita records centre receipt → received\nसुनीता केंद्र में दवा प्राप्त करती है"),
        ("d5_supply", "Sunita hands to Ramesh → supplied\nसुनीता रमेश को दवा देती है"),
        ("d5_closed", "Ramesh confirms → closed; audit trail\nरमेश पुष्टि करते हैं → मामला बंद"),
    ]),
]
D5_edges = [
    ("d5_report", "d5_verify", "case / मामला"),
    ("d5_verify", "d5_draft", "confirmed stockout / कमी की पुष्टि"),
    ("d5_draft", "d5_approve", "draft / मसौदा"),
    ("d5_approve", "d5_dispatch", "approved / मंज़ूर"),
    ("d5_dispatch", "d5_receive", "stock arrives / दवा आती है"),
    ("d5_receive", "d5_supply", "centre stock / केंद्र में स्टॉक"),
    ("d5_supply", "d5_closed", "patient confirms / रोगी पुष्टि"),
]
D5_classes = [("patient", "fill:#e6eedc,stroke:#6d8a5a,stroke-width:2px", ["d5_report", "d5_closed"])]

# D6 · The gate is evidence/ownership, not a date promised by the prototype.
D6_groups = [
    ("NOW", "BUILT PROTOTYPE / अभी बना · synthetic", [
        ("d6_now", "One fictional district; refill case, warnings, transfer draft, audit\nएक नमूना ज़िला; रिफ़िल मामला और रिकॉर्ड"),
        ("d6_nowgate", "Gate: real speech, usability and stock accuracy need field tests\nशर्त: असली आवाज़, उपयोग और स्टॉक जाँचें"),
    ]),
    ("PILOT", "NOT BUILT · Proposed district pilot / प्रस्तावित ज़िला पायलट", [
        ("d6_pilot", "Start one block, about 5–6 PHCs, inside a district\nएक ज़िले के एक ब्लॉक से शुरू करें"),
        ("d6_pilotgate", "Gate: consent; named custodian and transfer authority;\nresponse deadline; compare stockouts, patient receipt, staff time\nसहमति, ज़िम्मेदारी और असर मापें"),
    ]),
    ("STATE", "NOT BUILT · State rollout / राज्य विस्तार", [
        ("d6_state", "Authoritative stock import/export or register photo work;\ntraining, support, state drug lists and languages\nअसली स्टॉक डेटा, प्रशिक्षण, दवा और भाषा सेटिंग"),
        ("d6_stategate", "Gate: pilot evidence, state partner, manageable false alerts,\noverstock and staff time / शर्त: पायलट प्रमाण और राज्य साझेदार"),
    ]),
    ("NATION", "NOT BUILT · National rails / राष्ट्रीय जुड़ाव", [
        ("d6_rails", "DVDMS, NCD portal and ABDM/ABHA links\nमौजूदा स्वास्थ्य प्रणालियों से जुड़ाव"),
        ("d6_research", "Later research: doctor QR, meal/glucose diary, ASHA agents,\nfederated demand, MedGemma/PaliGemma; clinician review\nबाद का शोध; चिकित्सक समीक्षा ज़रूरी"),
        ("d6_railsgate", "Gate: partner access, privacy/identity rules, interoperability\nand evidence across states / साझेदार, निजता और कई राज्य"),
    ]),
]
D6_edges = [
    ("d6_now", "d6_nowgate", "test / जाँच"),
    ("d6_nowgate", "d6_pilot", "if ready / तैयार होने पर"),
    ("d6_pilot", "d6_pilotgate", "measure / मापें"),
    ("d6_pilotgate", "d6_state", "if benefit / लाभ होने पर"),
    ("d6_state", "d6_stategate", "repeat / दोहराएँ"),
    ("d6_stategate", "d6_rails", "if adopted / अपनाने पर"),
    ("d6_rails", "d6_research", "future work / आगे का काम"),
    ("d6_research", "d6_railsgate", "review / समीक्षा"),
]
D6_classes = [("roadmap", "fill:#f4e9da,stroke:#9c8069,stroke-dasharray:4 3", ["d6_pilot", "d6_pilotgate", "d6_state", "d6_stategate", "d6_rails", "d6_research", "d6_railsgate"])]

DIAGRAMS = [
    ("D1-REFILL-LOOP", "D1 · Ramesh's refill loop / रमेश की दवा का रास्ता", "BUILT PROTOTYPE · Five stages, four roles · Synthetic demo data", "TB", D1_groups, D1_edges, D1_classes, set()),
    ("D2-ARCHITECTURE", "D2 · Saathi architecture / साथी की बनावट", "BUILT PROTOTYPE · Vercel → Render → SQLite demo; offline writes replay later", "TB", D2_groups, D2_edges, D2_classes, D2_dashed),
    ("D3-AI-AND-HUMAN-GATES", "D3 · AI and human gates / एआई और इंसानी जाँच", "BUILT PROTOTYPE · Algorithms advise; people confirm and act", "TB", D3_groups, D3_edges, D3_classes, set()),
    ("D4-HIDDEN-DEMAND", "D4 · Hidden demand / छिपी ज़रूरत", "Synthetic simulation figures compare methods; shipped max rule has no measured field impact", "LR", list(reversed(D4_groups)), D4_edges, D4_classes, set()),
    ("D5-RAMESH-SEQUENCE", "D5 · One case to closed / एक मामला पूरा", "BUILT PROTOTYPE · Synthetic Ramesh/Nayagaon run; each arrow is a logged transition", "TB", D5_groups, D5_edges, D5_classes, set()),
    ("D6-SCALE-AND-ROADMAP", "D6 · Scale gates / विस्तार की शर्तें", "Only the first column is built; pilot, rollout, integrations and research are NOT BUILT", "TB", D6_groups, D6_edges, D6_classes, set()),
]

if __name__ == "__main__":
    for fname, title, subtitle, direction, groups, edges, classes, dashed in DIAGRAMS:
        page(fname, title, subtitle,
             flowchart(direction, groups, edges, classes=classes, dashed=dashed),
             spec(groups, edges))
