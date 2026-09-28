"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, Transfer } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useLoad, useRefData } from "@/lib/hooks";
import { PhoneShell } from "@/components/shells";
import { Bi, DrugName, ErrorBox, FacilityName, Icon, Loading, Status, when } from "@/components/ui";

/** Find a transfer: GET /transfers/{id}, or through the case that owns it (works before v0.5 lands). */
async function loadTransfer(id: string, facilityId: string): Promise<Transfer> {
  try {
    return await api.transfer(id);
  } catch {
    const cases = await api.cases({ facility_id: facilityId });
    const owner = cases.find((c) => c.transfer_id === id);
    if (!owner) throw new Error("Transfer not found");
    const detail = await api.caseDetail(owner.id);
    if (!detail.transfer) throw new Error("Transfer not found");
    return detail.transfer;
  }
}

export default function ReceiveTransfer() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const ref = useRefData();
  const t = useLoad(() => loadTransfer(id, user?.facility_id ?? ""), `tr-${id}`);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);

  const receive = async () => {
    setBusy(true);
    setErr(null);
    try {
      await api.receive(id);
      t.reload();
    } catch (e) {
      setErr(e);
    } finally {
      setBusy(false);
    }
  };

  const tr = t.data;
  const received = tr?.status === "received";
  return (
    <PhoneShell title={{ hi: "आ रहा स्टॉक", en: "Incoming stock" }} back="/pharmacist" tabs={false}
      foot={tr ? (received ? (
        <Link className="sa-btn sa-btn--hero" href={`/pharmacist/give/${tr.case_id}`} data-testid="go-give"><Icon name="hand-over" size={28} /><Bi hi="मरीज़ को दें" en="Give to patient" /></Link>
      ) : (
        <button type="button" className="sa-btn sa-btn--hero" data-testid="mark-received" disabled={busy || tr.status !== "dispatched"} onClick={receive}>
          <Icon name="check" size={28} /><Bi hi="स्टॉक मिल गया" en="Mark received" />
        </button>
      )) : undefined}>
      {!tr && (t.loading ? <Loading /> : <ErrorBox error={t.error} onRetry={t.reload} />)}
      {tr && (
        <>
          <section className="sa-card" style={{ gap: 12 }}>
            <div className="sa-card-head">
              <span style={{ font: "600 17px/24px var(--font-sans)", display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <FacilityName f={ref.facility(tr.from_facility_id)} id={tr.from_facility_id} /><Icon name="chevron-right" size={16} /><FacilityName f={ref.facility(tr.to_facility_id)} id={tr.to_facility_id} />
              </span>
              <span data-testid="transfer-status" data-status={tr.status}>
                {received ? <Status tone="ok" hi="मिल गया" en="Received" /> : tr.status === "dispatched" ? <Status tone="wait" icon="truck" hi="रास्ते में" en="On the way" /> : <Status tone="wait" hi="अभी भेजा नहीं" en="Not dispatched yet" />}
              </span>
            </div>
            <span className="m-heading" style={{ fontSize: 20 }}><span className="num">{tr.quantity}</span> · <DrugName d={ref.drug(tr.drug_id)} id={tr.drug_id} /></span>
            <span className="m-caption"><Bi inline hi={`मंज़ूर: ${when(tr.created_at).hi}`} en={`Drafted ${when(tr.created_at).en}`} /></span>
            {tr.batch_allocations && tr.batch_allocations.length > 0 && (
              <div className="sa-rows" style={{ boxShadow: "none" }}>
                {tr.batch_allocations.map((b) => (
                  <div key={b.batch_id} className="kv" style={{ padding: "8px 0" }}>
                    <span><Bi inline hi="बैच" en="Batch" /> <span className="num">{b.batch_id}</span></span>
                    <b className="num"><Bi inline hi={`${b.quantity} · समाप्ति ${b.expiry_date}`} en={`${b.quantity} · expires ${b.expiry_date}`} /></b>
                  </div>
                ))}
              </div>
            )}
          </section>
          {received && (
            <div className="sa-banner sa-banner--ok"><span className="sa-banner-ic"><Icon name="check-circle" /></span><Bi hi="स्टॉक आ गया। अब मरीज़ को दवा दें।" en="Stock is in. Now hand the medicine to the patient." /></div>
          )}
        </>
      )}
      {err ? <ErrorBox error={err} /> : null}
    </PhoneShell>
  );
}
