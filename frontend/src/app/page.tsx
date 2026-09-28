"use client";

import Link from "next/link";
import { Bi, DemoBadge, Icon, LangToggle } from "@/components/ui";

const NUMBERS = [
  { n: "10.1", hi: "लोगों को डायबिटीज़ है", en: "people live with diabetes", src: "ICMR–INDIAB-17, Lancet Diabetes & Endocrinology, 2023" },
  { n: "31.5", hi: "लोगों को हाई बीपी है", en: "people live with high blood pressure", src: "ICMR–INDIAB-17, Lancet Diabetes & Endocrinology, 2023" },
  { n: "8.64", hi: "सरकारी NCD कार्यक्रम में इलाज पा रहे हैं", en: "are under treatment in the national NCD programme", src: "PIB, 6 Mar 2026 (National NCD Portal)" },
];

const STEPS = [
  { hi: "बताएँ", en: "Report", dHi: "दवा नहीं मिली? मरीज़ या आशा बोलकर बता दें।", dEn: "Refill missed? The patient or ASHA just says it by voice.", icon: "mic" },
  { hi: "जाँचें", en: "Verify", dHi: "फ़ार्मासिस्ट अलमारी देखकर पक्का करते हैं।", dEn: "The pharmacist checks the shelf and confirms it.", icon: "check" },
  { hi: "चेतावनी", en: "Forecast & warn", dHi: "मरीज़ों की ज़रूरत बनाम स्टॉक — ख़त्म होने से पहले चेतावनी।", dEn: "Patients' need vs stock — a warning before it runs out.", icon: "alert" },
  { hi: "AI सुझाव, इंसान की मंज़ूरी", en: "AI drafts, a person approves", dHi: "पास के केंद्र से दवा भेजने का मसौदा — अधिकारी मंज़ूर करते हैं।", dEn: "A transfer from a nearby centre is drafted — the officer approves.", icon: "suggest" },
  { hi: "दवा मरीज़ तक", en: "Medicine reaches the patient", dHi: "दवा पहुँची, मरीज़ को सौंपी, मामला बंद।", dEn: "It arrives, is handed over, and the case closes.", icon: "hand-over" },
];

const ROLES = [
  { hi: "मरीज़", en: "Patient", who: "Ramesh, 54 · रमेश", art: "home", pHi: "बोलकर बताएँ कि दवा नहीं मिली", pEn: "Report a missed refill by voice" },
  { hi: "आशा", en: "ASHA worker", who: "Rekha · रेखा", art: "home", pHi: "अपने मरीज़ों की ओर से रिपोर्ट", pEn: "Report on a patient's behalf" },
  { hi: "फ़ार्मासिस्ट", en: "Pharmacist", who: "Sunita · सुनीता", art: "shelf", pHi: "एक टैप में जाँचें, दवा सौंपें", pEn: "Verify in one tap, hand over" },
  { hi: "ज़िला अधिकारी", en: "District officer", who: "Dr. Mehra · डॉ. मेहरा", art: "van", pHi: "चेतावनी देखें, ट्रांसफ़र मंज़ूर करें", pEn: "See warnings, approve transfers" },
];

export default function Landing() {
  return (
    <div className="sa-root" data-audience="desk" style={{ background: "var(--paper)", minHeight: "100dvh" }}>
      <header style={{ position: "sticky", top: 0, zIndex: 5, background: "var(--paper)", boxShadow: "inset 0 -1px 0 var(--line)" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "12px 16px", display: "flex", alignItems: "center", gap: 16 }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/art/logo.svg" alt="साथी Saathi" style={{ height: 36, width: "auto" }} />
          <span style={{ flex: 1 }} />
          <LangToggle />
          <Link className="sa-btn sa-btn--web" href="/login" data-testid="open-demo"><Bi hi="डेमो खोलें" en="Open demo" /></Link>
        </div>
      </header>

      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "0 16px 64px", display: "flex", flexDirection: "column", gap: 72 }}>
        <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 32, alignItems: "center", paddingTop: 48 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <span className="d-label muted"><Bi inline hi="सरकारी स्वास्थ्य केंद्रों के लिए" en="For government health centres" /></span>
            <h1 className="d-display hd" style={{ ["--bi-2nd" as string]: "26px" }}><Bi hi="दवा समय पर, घर तक" en="Every refill, reaching home" /></h1>
            <p className="d-body" style={{ fontSize: 18, lineHeight: "30px" }}>
              <Bi hi="डायबिटीज़ और बीपी के किसी मरीज़ को दवा के बिना घर न लौटना पड़े — साथी मरीज़, आशा, फ़ार्मासिस्ट और ज़िला अधिकारी को एक चक्र में जोड़ता है।" en="So no diabetes or blood-pressure patient goes home without their medicine — Saathi joins patients, ASHAs, pharmacists and district officers in one loop." />
            </p>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Link className="sa-btn" href="/login"><Bi hi="डेमो खोलें" en="Open demo" /><Icon name="chevron-right" /></Link>
              <a className="sa-btn sa-btn--outline" href="#how"><Bi hi="कैसे काम करता है" en="How it works" /></a>
            </div>
            <ul className="ticks">
              <li><Icon name="check-circle" size={20} /><Bi inline hi="डॉक्टरी सलाह नहीं" en="No medical advice" /></li>
              <li><Icon name="check-circle" size={20} /><Bi inline hi="हर AI सुझाव पर इंसान की मंज़ूरी" en="A person approves every AI suggestion" /></li>
              <li><Icon name="check-circle" size={20} /><Bi inline hi="नेट के बिना भी काम करता है" en="Works offline, sends later" /></li>
            </ul>
          </div>
          <div role="img" aria-label="Medicine travels from a stocked centre to Ramesh's home · दवा केंद्र से घर तक" style={{ position: "relative", minHeight: 380, borderRadius: 32, background: "var(--clay-100)", overflow: "hidden" }}>
            <div style={{ position: "absolute", left: -30, top: 30, width: 260, height: 260, borderRadius: "50%", background: "var(--marigold-100)" }} />
            <div style={{ position: "absolute", right: -30, bottom: -20, width: 280, height: 280, borderRadius: "50%", background: "var(--leaf-100)" }} />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/art/centre.webp" alt="" style={{ position: "absolute", left: "4%", top: "8%", width: "42%" }} />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/art/van.webp" alt="" style={{ position: "absolute", left: "34%", top: "46%", width: "30%" }} />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/art/home.webp" alt="" style={{ position: "absolute", right: "3%", top: "30%", width: "42%" }} />
            <span className="sa-status sa-status--ok" style={{ position: "absolute", left: 16, bottom: 16 }}><Icon name="truck" size={16} /><Bi inline hi="नयागाँव से सुंदरपुर, रास्ते में" en="Nayagaon → Sundarpur, on the way" /></span>
          </div>
        </section>

        <section style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <span className="d-label muted"><Bi inline hi="समस्या" en="The problem" /></span>
          <h2 className="d-h1 hd"><Bi hi="दवा है, पर हमेशा पहुँचती नहीं" en="The medicine exists. It doesn't always reach." /></h2>
          <div className="grid-kpi">
            {NUMBERS.map((x) => (
              <div key={x.n} className="sa-card sa-card--web" style={{ gap: 6 }}>
                <span className="d-display num" style={{ color: "var(--clay-700)" }}>{x.n} <span style={{ fontSize: 22 }}><Bi inline hi="करोड़" en="crore" /></span></span>
                <span className="d-body"><Bi hi={x.hi} en={x.en} /></span>
                <span className="d-caption">{x.src}</span>
              </div>
            ))}
          </div>
        </section>

        <section id="how" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <span className="d-label muted"><Bi inline hi="कैसे काम करता है" en="How it works" /></span>
          <h2 className="d-h1 hd"><Bi hi="पाँच कदम, एक चक्र" en="Five steps, one loop" /></h2>
          <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
            {STEPS.map((s, i) => (
              <li key={s.en} className="sa-card sa-card--web" style={{ gap: 10 }}>
                <span style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <span style={{ width: 36, height: 36, borderRadius: 12, background: "var(--clay-600)", color: "var(--on-clay)", display: "grid", placeItems: "center", font: "700 18px/1 var(--font-display)" }}>{i + 1}</span>
                  <Icon name={s.icon} />
                </span>
                <span className="d-h3"><Bi hi={s.hi} en={s.en} /></span>
                <span className="d-body-sm"><Bi hi={s.dHi} en={s.dEn} /></span>
              </li>
            ))}
          </ol>
        </section>

        <section style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <span className="d-label muted"><Bi inline hi="किसके लिए" en="Who it's for" /></span>
          <h2 className="d-h1 hd"><Bi hi="चार लोग, एक ही मक़सद" en="Four people, one purpose" /></h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            {ROLES.map((r) => (
              <div key={r.en} className="sa-card sa-card--web" style={{ gap: 10 }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={`/art/${r.art}.webp`} alt="" style={{ width: 88, height: 88, objectFit: "contain" }} />
                <span className="d-h3"><Bi hi={r.hi} en={r.en} /></span>
                <span className="d-caption">{r.who}</span>
                <span className="d-body-sm"><Bi hi={r.pHi} en={r.pEn} /></span>
              </div>
            ))}
          </div>
        </section>

        <section className="sa-card sa-card--web" style={{ gap: 16 }}>
          <h2 className="d-h2"><Bi hi="दो वादे जो हम कभी नहीं तोड़ते" en="Two promises we never break" /></h2>
          <div className="grid-2">
            <p className="d-body"><b><Bi hi="साथी कभी डॉक्टरी सलाह नहीं देता।" en="Saathi never gives medical advice." /></b> <Bi hi="सिर्फ़ यह देखता है कि दवा आप तक पहुँची या नहीं। खुराक हमेशा डॉक्टर तय करते हैं।" en="It only tracks whether your medicine reached you. Doses always stay with your doctor." /></p>
            <p className="d-body"><b><Bi hi="हर AI सुझाव पर इंसान की मंज़ूरी।" en="A person approves every AI suggestion." /></b> <Bi hi="जब तक ज़िला अधिकारी मंज़ूर न करें, कुछ नहीं हिलता — और हर कदम रिकॉर्ड होता है।" en="Nothing moves until the district officer approves — and every step is recorded." /></p>
          </div>
        </section>

        <section style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }} className="bi-c">
          <h2 className="d-h1 hd"><Bi hi="रमेश जी की कहानी देखिए" en="Walk through Ramesh's story" /></h2>
          <p className="d-body"><Bi hi="मेटफॉर्मिन ख़त्म → बोलकर बताया → दवा घर तक।" en="Metformin ran out → reported by voice → medicine back in hand." /></p>
          <Link className="sa-btn" href="/login"><Bi hi="डेमो खोलें" en="Open demo" /><Icon name="chevron-right" /></Link>
          <DemoBadge long />
          <p className="d-caption"><Bi inline hi="डेमो में कोई असली मरीज़ डेटा नहीं है।" en="No real patient data is used in this demo." /></p>
        </section>
      </main>
    </div>
  );
}
