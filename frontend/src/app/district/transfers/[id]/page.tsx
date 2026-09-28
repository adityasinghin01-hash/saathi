"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, Transfer } from "@/lib/api";
import { useLoad, useRefData } from "@/lib/hooks";
import { useLanguage } from "@/i18n/LanguageProvider";
import { WebShell } from "@/components/shells";
import { TRANSFER_STATUS, useDistrict } from "@/components/district";
import { AiBadge, Bi, DrugName, ErrorBox, FacilityName, Icon, Loading, Status, hiName, when } from "@/components/ui";



async function loadTransfer(id: string): Promise<Transfer> {
  try {
    return await api.transfer(id);
  } catch {
    const owner = (await api.cases()).find((c) => c.transfer_id === id);
    const t = owner ? (await api.caseDetail(owner.id)).transfer : null;
    if (!t) throw new Error("Transfer not found");
    return t;
  }
}

const CHECKS: { k: keyof Transfer["constraints_checked"]; hi: string; en: string; whyHi: string; whyEn: string }[] = [
  { k: "donor_safety_stock_ok", hi: "दाता का सुरक्षित स्टॉक बचा", en: "Donor keeps its safety stock", whyHi: "भेजने के बाद भी दाता के पास अपने 14 दिन की दवा रहती है।", whyEn: "After sending, the donor still holds 14 days for its own patients." },
  { k: "expiry_ok", hi: "इस्तेमाल से पहले कोई बैच ख़राब नहीं", en: "No batch expires before use", whyHi: "सिर्फ़ वे बैच जो पहुँचने के 30+ दिन बाद तक चलें।", whyEn: "Only batches that stay valid 30+ days after arrival." },
  { k: "units_ok", hi: "इकाई एक जैसी", en: "Units match", whyHi: "दोनों केंद्र एक ही दवा, एक ही ताक़त, गोलियों में गिनते हैं।", whyEn: "Same medicine, same strength, both counted in tablets." },
];

export default function TransferReview() {
  const { id } = useParams<{ id: string }>();
  const district = useDistrict();
  const ref = useRefData();
  const { both } = useLanguage();
  const t = useLoad(async () => {
    const tr = await loadTransfer(id);
    const rows = district ? await api.overview(district).catch(() => []) : [];
    const donor = rows.find((r) => r.facility_id === tr.from_facility_id && r.drug_id === tr.drug_id);
    const target = rows.find((r) => r.facility_id === tr.to_facility_id && r.drug_id === tr.drug_id);
    return { tr, donor, target };
  }, `trv-${id}-${district}`);
  const [busy, setBusy] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [note, setNote] = useState("");
  const [err, setErr] = useState<unknown>(null);

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setErr(null);
    try {
      await fn();
      setRejecting(false);
      t.reload();
    } catch (e) {
      setErr(e);
    } finally {
      setBusy(false);
    }
  };

  const tr = t.data?.tr;
  const s = tr ? TRANSFER_STATUS[tr.status] : null;
  const perDay = (r?: { combined: number; horizon_days: number }) => (r && r.horizon_days ? r.combined / r.horizon_days : 0);
  const daysOf = (units: number, r?: { combined: number; horizon_days: number }) => { const p = perDay(r); return p > 0 ? Math.round(units / p) : null; };

  return (
    <WebShell title={{ hi: "स्थानांतरण", en: "Transfer" }}>
      <nav aria-label="Breadcrumb · रास्ता" className="d-caption"><Link className="lnk" href="/district/transfers"><Bi inline hi="स्थानांतरण" en="Transfers" /></Link> / {id.slice(0, 18)}</nav>
      {!tr && (t.loading ? <Loading /> : <ErrorBox error={t.error} onRetry={t.reload} />)}
      {tr && s && (
        <>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 16, flexWrap: "wrap" }}>
            <h1 className="d-h1 hd"><Bi hi={`स्थानांतरण · ${hiName(ref.drug(tr.drug_id), "drug")}`} en={`Transfer · ${ref.drug(tr.drug_id)?.name ?? tr.drug_id} ${ref.drug(tr.drug_id)?.strength ?? ""}`} /></h1>
            <span className="d-caption"><Bi inline hi={`मसौदा ${when(tr.created_at).hi}`} en={`Drafted ${when(tr.created_at).en}`} /></span>
          </div>

          <section className="sa-card sa-card--web sa-card--suggest" style={{ gap: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              {tr.drafted_by === "agent" ? <AiBadge source={tr.ai_source} model={tr.ai_model} /> : <span className="d-label"><Bi inline hi="अधिकारी द्वारा" en="Drafted by officer" /></span>}
              <span data-testid="transfer-status" data-status={tr.status}><Status tone={s.tone} icon={s.icon} hi={s.hi} en={s.en} large /></span>
            </div>

            <div className="grid-2" style={{ gridTemplateColumns: "1fr auto 1fr", alignItems: "center" }}>
              <div className="sa-card" style={{ gap: 4, boxShadow: "none", background: "var(--paper)" }}>
                <span className="d-caption"><Bi inline hi="कहाँ से" en="FROM" /></span>
                <span className="d-h3"><FacilityName f={ref.facility(tr.from_facility_id)} id={tr.from_facility_id} inline={false} /></span>
                {t.data?.donor && <span className="d-body-sm num"><Bi inline hi={`${Math.round(t.data.donor.on_hand)} → ${Math.round(t.data.donor.on_hand - tr.quantity)} गोलियाँ`} en={`${Math.round(t.data.donor.on_hand)} → ${Math.round(t.data.donor.on_hand - tr.quantity)} tablets`} /></span>}
                {t.data?.donor && daysOf(t.data.donor.on_hand - tr.quantity, t.data.donor) !== null && <span className="d-caption"><Bi inline hi={`भेजने के बाद ~${daysOf(t.data.donor.on_hand - tr.quantity, t.data.donor)} दिन बचेंगे`} en={`~${daysOf(t.data.donor.on_hand - tr.quantity, t.data.donor)} days left after sending`} /></span>}
              </div>
              <Icon name="chevron-right" size={32} style={{ color: "var(--clay-600)" }} />
              <div className="sa-card" style={{ gap: 4, boxShadow: "none", background: "var(--paper)" }}>
                <span className="d-caption"><Bi inline hi="कहाँ" en="TO" /></span>
                <span className="d-h3"><FacilityName f={ref.facility(tr.to_facility_id)} id={tr.to_facility_id} inline={false} /></span>
                {t.data?.target && <span className="d-body-sm num"><Bi inline hi={`${Math.round(t.data.target.on_hand)} → ${Math.round(t.data.target.on_hand + tr.quantity)} गोलियाँ`} en={`${Math.round(t.data.target.on_hand)} → ${Math.round(t.data.target.on_hand + tr.quantity)} tablets`} /></span>}
              </div>
            </div>

            <div className="grid-2">
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span className="d-caption"><Bi inline hi="मात्रा" en="QUANTITY" /></span>
                <span className="d-kpi num" data-testid="transfer-qty">{tr.quantity}</span>
                <span className="d-caption"><DrugName d={ref.drug(tr.drug_id)} id={tr.drug_id} /></span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span className="d-caption"><Bi inline hi="बैच" en="BATCHES" /></span>
                {(tr.batch_allocations ?? tr.batch_ids.map((b) => ({ batch_id: b, quantity: tr.quantity, expiry_date: "—" }))).map((b) => (
                  <div key={b.batch_id} className="bt" style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                    <span className="num">{b.batch_id}</span><span className="num"><Bi inline hi={`समाप्ति ${b.expiry_date}`} en={`expires ${b.expiry_date}`} /></span><b className="num">{b.quantity}</b>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <span className="d-caption"><Bi inline hi="तीन जाँच" en="THREE CHECKS" /></span>
              {CHECKS.map((c) => {
                const ok = tr.constraints_checked[c.k];
                return (
                  <div key={c.k} className="chk" style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                    <Icon name={ok ? "check-circle" : "out-of-stock"} style={{ color: ok ? "var(--status-ok)" : "var(--status-out)", flex: "none" }} />
                    <span><span className="d-label"><Bi inline hi={c.hi} en={c.en} /></span><span className="d-caption" style={{ display: "block" }}><Bi inline hi={c.whyHi} en={c.whyEn} /></span></span>
                  </div>
                );
              })}
            </div>

            <div className="why" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span className="d-caption"><Bi inline hi={tr.ai_source === "gemini" ? "AI का कारण" : "कारण"} en={tr.ai_source === "gemini" ? "WHY THE AI SUGGESTS THIS" : "WHY"} /></span>
              <p className="d-body" data-testid="rationale" style={{ margin: 0 }}>{tr.rationale}</p>
            </div>

            {err ? <ErrorBox error={err} /> : null}

            {tr.status === "draft" && (
              <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                <button type="button" className="sa-btn sa-btn--web" data-testid="approve" disabled={busy} onClick={() => act(() => api.approve(id))}><Icon name="check" size={20} /><Bi hi="मंज़ूर करें" en="Approve transfer" /></button>
                <button type="button" className="sa-btn sa-btn--web sa-btn--outline" aria-expanded={rejecting} disabled={busy} onClick={() => setRejecting((r) => !r)}><Icon name="close" size={20} /><Bi hi="रद्द करें" en="Reject" /></button>
                <span className="d-caption"><Bi inline hi="आपका नाम और समय रिकॉर्ड होगा।" en="Your name and time go into the audit trail." /></span>
              </div>
            )}
            {tr.status === "draft" && rejecting && (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <label className="sa-field">
                  <span className="sa-field-label"><Bi hi="रद्द करने का कारण (ज़रूरी)" en="Why are you rejecting? (required)" /></span>
                  <span className="sa-input sa-input--web" style={{ alignItems: "flex-start" }}><textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder={both("जैसे: अगले हफ़्ते नयागाँव में कैंप है", "e.g. Nayagaon has a camp next week")} /></span>
                </label>
                <div style={{ display: "flex", gap: 8 }}>
                  <button type="button" className="sa-btn sa-btn--web sa-btn--danger" disabled={!note.trim() || busy} onClick={() => act(() => api.reject(id, note.trim()))}><Bi hi="रद्द भेजें" en="Send rejection" /></button>
                  <button type="button" className="sa-btn sa-btn--web sa-btn--ghost" onClick={() => setRejecting(false)}><Bi hi="रहने दें" en="Cancel" /></button>
                </div>
              </div>
            )}
            {tr.status === "approved" && (
              <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                <button type="button" className="sa-btn sa-btn--web" data-testid="dispatch" disabled={busy} onClick={() => act(() => api.dispatch(id))}><Icon name="truck" size={20} /><Bi hi="भेज दिया गया" en="Mark dispatched" /></button>
                <span className="d-caption"><Bi inline hi="गाड़ी निकलने पर दबाएँ" en="Press when the van leaves" /></span>
              </div>
            )}
            {(tr.status === "dispatched" || tr.status === "received") && (
              <p className="d-body-sm"><Bi inline hi={tr.status === "received" ? "स्टॉक पहुँच गया। फ़ार्मासिस्ट मरीज़ को दवा देंगे।" : "रास्ते में — प्राप्त करने वाले फ़ार्मासिस्ट पुष्टि करेंगे।"} en={tr.status === "received" ? "Stock arrived. The pharmacist will hand it to the patient." : "On the way — the receiving pharmacist confirms arrival."} /></p>
            )}
          </section>
        </>
      )}
    </WebShell>
  );
}
