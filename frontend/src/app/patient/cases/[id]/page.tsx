"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, CaseDetail, CaseStatus } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useLoad, useRefData } from "@/lib/hooks";
import { PhoneShell } from "@/components/shells";
import { Bi, CaseStatusChip, DemoBadge, DrugName, ErrorBox, FacilityName, Icon, Loading, hiName, when } from "@/components/ui";

const ORDER: CaseStatus[] = ["reported", "verified", "transfer_drafted", "transfer_approved", "dispatched", "received", "partially_supplied", "supplied", "closed"];
const rank = (s: CaseStatus) => ORDER.indexOf(s);

const STEPS: { hi: string; en: string; icon: string; reachedAt: CaseStatus[] }[] = [
  { hi: "शिकायत दर्ज", en: "Reported", icon: "mic", reachedAt: ["reported"] },
  { hi: "फ़ार्मासिस्ट ने जाँचा", en: "Verified by pharmacist", icon: "check", reachedAt: ["verified"] },
  { hi: "दवा रास्ते में", en: "Transfer on the way", icon: "truck", reachedAt: ["transfer_drafted", "transfer_approved", "dispatched"] },
  { hi: "केंद्र पहुँची", en: "Arrived at centre", icon: "health-centre", reachedAt: ["received"] },
  { hi: "आपको मिली", en: "Given to you", icon: "hand-over", reachedAt: ["partially_supplied", "supplied"] },
  { hi: "मामला बंद", en: "Closed", icon: "check-circle", reachedAt: ["closed"] },
];

function nextLine(c: CaseDetail): { hi: string; en: string } {
  switch (c.status) {
    case "reported": return { hi: "आगे क्या: फ़ार्मासिस्ट स्टॉक देखकर पक्का करेंगे।", en: "Next: the pharmacist checks the shelf and confirms." };
    case "verified": return c.verification.result === "stock_available"
      ? { hi: "आगे क्या: केंद्र पर दवा है — जाकर ले लें।", en: "Next: the centre has it — collect it there." }
      : { hi: "आगे क्या: ज़िला अधिकारी पास के केंद्र से दवा मँगवा रहे हैं।", en: "Next: the district is arranging medicine from a nearby centre." };
    case "transfer_drafted":
    case "transfer_approved": return { hi: "आगे क्या: पास के केंद्र से दवा भेजी जा रही है।", en: "Next: a nearby centre is sending the medicine." };
    case "dispatched": return { hi: "आगे क्या: दवा रास्ते में है। पहुँचते ही बताएँगे।", en: "Next: the medicine is on the way. We'll tell you when it arrives." };
    case "received": return { hi: "आगे क्या: दवा केंद्र पर आ गई — ले लीजिए।", en: "Next: it's at your centre — please collect it." };
    case "partially_supplied": return { hi: "कुछ दवा मिली, बाकी जल्द।", en: "You got part of it; the rest is coming." };
    case "supplied": return { hi: "दवा मिल गई? नीचे बटन दबाएँ।", en: "Got it? Tap the button below." };
    default: return { hi: "", en: "" };
  }
}

export default function CasePage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const ref = useRefData();
  const detail = useLoad(() => api.caseDetail(id), `case-${id}`);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);
  const c = detail.data;
  const back = user?.role === "asha" ? "/asha" : "/patient";

  const confirm = async () => {
    setBusy(true);
    setErr(null);
    try {
      await api.confirmReceived(id);
      detail.reload();
    } catch (e) {
      setErr(e);
    } finally {
      setBusy(false);
    }
  };

  if (!c) {
    return (
      <PhoneShell title={{ hi: "मेरी शिकायत", en: "My report" }} back={back}>
        {detail.loading ? <Loading /> : <ErrorBox error={detail.error} onRetry={detail.reload} />}
      </PhoneShell>
    );
  }

  /* ---------- closed: the calm end of the story ---------- */
  if (c.status === "closed") {
    const handed = c.events.filter((e) => e.to_status === "supplied" || e.to_status === "partially_supplied").at(-1);
    const w = handed ? when(handed.at) : null;
    return (
      <PhoneShell title={{ hi: "मेरी शिकायत", en: "My report" }} back={back}
        foot={<Link className="sa-btn sa-btn--hero" href={back}><Icon name="home" size={28} /><Bi hi="घर पर जाएँ" en="Go home" /></Link>}>
        <div className="bi-c" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, textAlign: "center", paddingTop: 8 }}>
          <div style={{ width: 176, height: 176, borderRadius: "50%", background: "var(--leaf-100)", display: "grid", placeItems: "center" }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/art/medkit.webp" alt="" style={{ width: 150, height: 150, objectFit: "contain" }} />
          </div>
          <h1 className="m-display hd" data-testid="closed-title" style={{ ["--bi-2nd" as string]: "18px" }}><Bi hi="आपकी दवा मिल गई" en="You have your medicine" /></h1>
          <CaseStatusChip status={c.status} />
        </div>
        <section className="sa-card" style={{ gap: 0, padding: "8px 16px" }}>
          <div className="kv"><Bi hi="दवा" en="Medicine" /><b><DrugName d={ref.drug(c.drug_id)} id={c.drug_id} /></b></div>
          <div className="kv"><Bi hi="मिली / माँगी" en="Given / asked" /><b className="num">{c.received_qty} / {c.requested_qty}</b></div>
          <div className="kv"><Bi hi="कहाँ" en="Where" /><b><FacilityName f={ref.facility(c.facility_id)} id={c.facility_id} /></b></div>
          {w && <div className="kv"><Bi hi="कब" en="When" /><b><Bi inline hi={w.hi} en={w.en} /></b></div>}
        </section>
        <div className="sa-banner sa-banner--ok"><span className="sa-banner-ic"><Icon name="check-circle" /></span><Bi hi="धन्यवाद। मामला बंद हो गया।" en="Thank you. Your case is closed." /></div>
      </PhoneShell>
    );
  }

  const r = rank(c.status);
  const next = nextLine(c);
  const canConfirm = c.status === "supplied" || c.status === "partially_supplied";
  const stepState = (i: number): "is-done" | "is-current" | "is-waiting" => {
    const reached = STEPS[i].reachedAt.some((s) => rank(s) <= r) || STEPS.slice(i + 1).some((st) => st.reachedAt.some((s) => rank(s) <= r));
    const current = STEPS[i].reachedAt.includes(c.status);
    return current ? "is-current" : reached ? "is-done" : "is-waiting";
  };
  const stepTime = (i: number) => {
    const ev = c.events.filter((e) => STEPS[i].reachedAt.includes(e.to_status as CaseStatus)).at(-1);
    return ev ? when(ev.at) : null;
  };

  return (
    <PhoneShell title={{ hi: "मेरी शिकायत", en: "My report" }} back={back}
      foot={canConfirm ? (
        <button type="button" className="sa-btn sa-btn--hero" data-testid="got-it" disabled={busy} onClick={confirm}>
          <Icon name="check" size={28} /><Bi hi="हाँ, मुझे मिल गई" en="Yes, I received it" />
        </button>
      ) : undefined}>
      <section className="sa-card" style={{ gap: 10 }}>
        <div className="sa-card-head">
          <span style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <span style={{ width: 44, height: 44, borderRadius: 14, background: "var(--clay-100)", color: "var(--clay-ink)", display: "grid", placeItems: "center", flex: "none" }}><Icon name="medicines" /></span>
            <span style={{ font: "600 18px/26px var(--font-sans)", ["--bi-2nd" as string]: "13px" }}><DrugName d={ref.drug(c.drug_id)} id={c.drug_id} inline={false} /></span>
          </span>
          <DemoBadge />
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <CaseStatusChip status={c.status} />
          <span className="m-caption">{hiName(ref.facility(c.facility_id), "facility")} · {ref.facility(c.facility_id)?.name}</span>
        </div>
      </section>

      {next.en && (
        <div className="sa-banner" style={{ background: "var(--marigold-100)", color: "var(--ink)", alignItems: "flex-start" }}>
          <span className="sa-banner-ic" style={{ background: "var(--paper-raised)" }}><Icon name="clock" /></span>
          <Bi hi={next.hi} en={next.en} />
        </div>
      )}
      {err ? <ErrorBox error={err} /> : null}

      <ol className="sa-steps" aria-label="Case steps · मामले के कदम" style={{ padding: "4px 4px 0" }}>
        {STEPS.map((s, i) => {
          const st = stepState(i);
          const t = stepTime(i);
          return (
            <li key={s.en} className={`sa-step ${st}`} aria-current={st === "is-current" ? "step" : undefined}>
              <span className="sa-step-dot"><Icon name={st === "is-done" ? "check" : s.icon} size={20} /></span>
              <div className="sa-step-body">
                <div className="sa-step-title"><Bi hi={s.hi} en={s.en} /></div>
                {t && <div className="sa-step-meta"><Bi hi={t.hi} en={t.en} /></div>}
              </div>
            </li>
          );
        })}
      </ol>
      {c.transcript && (
        <section className="sa-card" style={{ gap: 6 }}>
          <span className="m-caption" style={{ fontWeight: 600 }}><Bi inline hi="आपने कहा" en="What you said" /></span>
          <p style={{ margin: 0, font: "400 16px/26px var(--font-hindi)" }}>{c.transcript}</p>
        </section>
      )}
    </PhoneShell>
  );
}
