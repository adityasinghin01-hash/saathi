"use client";

import Link from "next/link";
import { api, Transfer } from "@/lib/api";
import { useLoad, useRefData } from "@/lib/hooks";
import { WebShell } from "@/components/shells";
import { TRANSFER_STATUS } from "@/components/district";
import { Bi, DrugName, Empty, ErrorBox, FacilityName, Loading, Status, when } from "@/components/ui";

const COLS: Transfer["status"][] = ["draft", "approved", "dispatched", "received"];

/** All transfers: GET /transfers, or collected from cases before v0.5 lands. */
async function loadAll(): Promise<Transfer[]> {
  try {
    return await api.transfers();
  } catch {
    const cases = (await api.cases()).filter((c) => c.transfer_id);
    const details = await Promise.all(cases.map((c) => api.caseDetail(c.id)));
    return details.flatMap((d) => (d.transfer ? [d.transfer] : []));
  }
}

export default function TransfersPage() {
  const ref = useRefData();
  const list = useLoad(loadAll, "transfers");
  const all = list.data ?? [];
  return (
    <WebShell title={{ hi: "स्थानांतरण", en: "Transfers" }}>
      <h1 className="d-h1 hd"><Bi hi="स्थानांतरण" en="Transfers" /></h1>
      {list.loading && !list.data && <Loading />}
      {list.error ? <ErrorBox error={list.error} onRetry={list.reload} /> : null}
      {list.data && all.length === 0 && <Empty hi="अभी कोई स्थानांतरण नहीं" en="No transfers yet" art="van" />}
      {all.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16, alignItems: "start" }}>
          {COLS.map((st) => {
            const s = TRANSFER_STATUS[st];
            const items = all.filter((t) => t.status === st);
            return (
              <section key={st} className="col" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <div className="colh" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <Status tone={s.tone} icon={s.icon} hi={s.hi} en={s.en} /><span className="sa-count">{items.length}</span>
                </div>
                {items.map((t) => (
                  <Link key={t.id} href={`/district/transfers/${t.id}`} className="sa-card sa-card--action" style={{ gap: 6 }} data-testid={`transfer-card-${t.id}`}>
                    <span className="d-label"><DrugName d={ref.drug(t.drug_id)} id={t.drug_id} /> · <span className="num">{t.quantity}</span></span>
                    <span className="d-caption"><FacilityName f={ref.facility(t.from_facility_id)} id={t.from_facility_id} /> → <FacilityName f={ref.facility(t.to_facility_id)} id={t.to_facility_id} /></span>
                    <span className="d-caption"><Bi inline hi={when(t.created_at).hi} en={when(t.created_at).en} /></span>
                  </Link>
                ))}
              </section>
            );
          })}
        </div>
      )}
    </WebShell>
  );
}
