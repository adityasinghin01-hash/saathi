"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useOfflineQueue } from "@/lib/OfflineQueueContext";
import { useLoad, useRefData } from "@/lib/hooks";
import { PhoneShell } from "@/components/shells";
import { Bi, DataAge, DemoBadge, DrugName, ErrorBox, FacilityName, Icon, Loading, Stepper, useNow } from "@/components/ui";

export default function StockPage() {
  const { user } = useAuth();
  const { isOffline, enqueue } = useOfflineQueue();
  const ref = useRefData();
  const now = useNow();
  const fid = user?.facility_id ?? "";
  const snaps = useLoad(() => api.stock(fid).catch(() => []), `stock-${fid}`);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [state, setState] = useState<"idle" | "saving" | "saved" | "offline">("idle");
  const [err, setErr] = useState<unknown>(null);

  const drugs = ref.data?.drugs ?? [];
  const last = (drugId: string) => snaps.data?.find((s) => s.drug_id === drugId);
  const changed = Object.keys(counts).filter((k) => counts[k] !== (last(k)?.on_hand ?? 0));

  const save = async () => {
    setState("saving");
    setErr(null);
    try {
      for (const drugId of changed) {
        const prev = last(drugId);
        const expiry = prev?.batches?.map((b) => b.expiry_date).sort().at(-1) ?? new Date(Date.now() + 365 * 864e5).toISOString().slice(0, 10);
        const body = {
          facility_id: fid, drug_id: drugId, on_hand: counts[drugId],
          batches: [{ id: `count-${fid}-${drugId}-${Date.now()}`, facility_id: fid, drug_id: drugId, quantity: counts[drugId], expiry_date: expiry }],
        };
        if (isOffline) await enqueue({ method: "POST", path: "/stock", body });
        else await api.postStock(body);
      }
      setState(isOffline ? "offline" : "saved");
      setCounts({});
      snaps.reload();
    } catch (e) {
      setErr(e);
      setState("idle");
    }
  };

  return (
    <PhoneShell title={{ hi: "स्टॉक", en: "Stock" }}
      foot={<button type="button" className="sa-btn sa-btn--hero" data-testid="save-stock" disabled={changed.length === 0 || state === "saving"} onClick={save}><Icon name="check" size={28} /><Bi hi="गिनती सेव करें" en="Save count" /></button>}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <span className="m-caption"><FacilityName f={ref.facility(fid)} id={fid} /> · <Bi inline hi="हर अलमारी गिनें" en="count each shelf" /></span>
        <DemoBadge />
      </div>
      {state === "offline" && <div className="sa-banner sa-banner--offline"><span className="sa-banner-ic"><Icon name="cloud-off" /></span><Bi hi="फ़ोन में सेव — नेट आते ही भेज देंगे" en="Saved offline — will send when online" /></div>}
      {state === "saved" && <div className="sa-banner sa-banner--ok" data-testid="stock-saved"><span className="sa-banner-ic"><Icon name="check-circle" /></span><Bi hi="गिनती सेव हो गई" en="Count saved" /></div>}
      {err ? <ErrorBox error={err} /> : null}
      {(ref.loading || snaps.loading) && !ref.data && <Loading />}
      {drugs.map((d) => {
        const s = last(d.id);
        const value = counts[d.id] ?? s?.on_hand ?? 0;
        return (
          <section key={d.id} className="sa-card sk" style={{ gap: 10 }}>
            <div className="sa-card-head">
              <span style={{ font: "600 17px/24px var(--font-sans)" }}><DrugName d={d} id={d.id} inline={false} /></span>
              {s && <DataAge iso={s.recorded_at} now={now} />}
            </div>
            {s && <span className="m-caption"><Bi inline hi={`पिछली गिनती ${s.on_hand}`} en={`last count ${s.on_hand}`} /></span>}
            <Stepper value={value} onChange={(v) => setCounts((c) => ({ ...c, [d.id]: v }))} step={10} label={{ hi: "गोलियाँ", en: "Tablets" }} testId={`stock-${d.id}`} />
          </section>
        );
      })}
    </PhoneShell>
  );
}
