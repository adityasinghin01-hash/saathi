"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useLoad, useRefData } from "@/lib/hooks";
import { PhoneShell } from "@/components/shells";
import { Bi, CaseStatusChip, DrugName, ErrorBox, Icon, Loading, Status, Stepper, hiName } from "@/components/ui";

export default function GivePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const ref = useRefData();
  const detail = useLoad(async () => {
    const c = await api.caseDetail(id);
    const patient = await api.patient(c.patient_id).catch(() => null);
    return { c, patient };
  }, `give-${id}`);
  const [qty, setQty] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);

  const c = detail.data?.c;
  const owed = c ? Math.max(0, c.requested_qty - c.received_qty) : 0;
  const give = qty ?? owed;
  const canGive = c && ["received", "partially_supplied", "verified"].includes(c.status);

  const submit = async () => {
    setBusy(true);
    setErr(null);
    try {
      await api.supply(id, give);
      router.push("/pharmacist");
    } catch (e) {
      setErr(e);
      setBusy(false);
    }
  };

  return (
    <PhoneShell title={{ hi: "मरीज़ को दें", en: "Give to patient" }} back="/pharmacist" tabs={false}
      foot={canGive ? (
        <button type="button" className="sa-btn sa-btn--hero" data-testid="hand-over" disabled={busy || give < 1} onClick={submit}>
          <Icon name="hand-over" size={28} /><Bi hi="दवा सौंपें" en="Hand over medicine" />
        </button>
      ) : undefined}>
      {!c && (detail.loading ? <Loading /> : <ErrorBox error={detail.error} onRetry={detail.reload} />)}
      {c && (
        <>
          <section className="sa-card" style={{ gap: 12 }}>
            <div className="sa-card-head">
              <span style={{ font: "600 17px/24px var(--font-sans)" }}>
                {detail.data?.patient ? <Bi hi={`${hiName(detail.data.patient)}, ${detail.data.patient.age}`} en={`${detail.data.patient.name}, ${detail.data.patient.age}`} /> : c.patient_id}
              </span>
              <CaseStatusChip status={c.status} />
            </div>
            <div className="kv"><Bi hi="दवा" en="Medicine" /><b><DrugName d={ref.drug(c.drug_id)} id={c.drug_id} /></b></div>
            <div className="kv"><Bi hi="माँगी / अब तक दी" en="Asked / given so far" /><b className="num">{c.requested_qty} / {c.received_qty}</b></div>
          </section>
          {canGive ? (
            <section className="sa-card" style={{ gap: 12 }}>
              <span className="m-caption" style={{ fontWeight: 600 }}><Bi inline hi="अभी कितनी दें" en="Tablets to give now" /></span>
              <Stepper value={give} onChange={setQty} step={10} min={1} label={{ hi: "कितनी दें", en: "Tablets to give" }} testId="give-qty" />
              <span style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <span className="m-body num"><Bi inline hi={`दी ${c.received_qty + give} / माँगी ${c.requested_qty}`} en={`Given ${c.received_qty + give} / asked ${c.requested_qty}`} /></span>
                {c.received_qty + give >= c.requested_qty ? <Status tone="ok" hi="पूरी" en="Full" /> : <Status tone="low" hi={`${c.requested_qty - c.received_qty - give} बाकी`} en={`${c.requested_qty - c.received_qty - give} still owed`} />}
              </span>
              <p className="m-caption"><Bi hi="कम देना ठीक है — बाकी के लिए मामला खुला रहेगा।" en="Partial is fine — the case stays open for what's still owed." /></p>
            </section>
          ) : (
            <div className="sa-banner"><span className="sa-banner-ic"><Icon name="clock" /></span><Bi hi="अभी देने लायक स्थिति नहीं" en="Not ready to hand over yet" /></div>
          )}
        </>
      )}
      {err ? <ErrorBox error={err} /> : null}
    </PhoneShell>
  );
}
