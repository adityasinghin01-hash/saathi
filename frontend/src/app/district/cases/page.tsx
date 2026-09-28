"use client";

import { useState } from "react";
import { api, CaseStatus } from "@/lib/api";
import { useLoad, usePatientNames, useRefData } from "@/lib/hooks";
import { useLanguage } from "@/i18n/LanguageProvider";
import { WebShell } from "@/components/shells";
import { Bi, CASE_STATUS, CaseStatusChip, DrugName, Empty, ErrorBox, FacilityName, Icon, Loading, age, initials, useNow, when } from "@/components/ui";

const COLUMNS: { hi: string; en: string; statuses: CaseStatus[] }[] = [
  { hi: "दर्ज", en: "Reported", statuses: ["reported"] },
  { hi: "जाँचा", en: "Verified", statuses: ["verified"] },
  { hi: "ट्रांसफ़र", en: "Transfer", statuses: ["transfer_drafted", "transfer_approved", "dispatched"] },
  { hi: "केंद्र पर", en: "At centre", statuses: ["received", "partially_supplied"] },
  { hi: "दी गई", en: "Supplied", statuses: ["supplied"] },
  { hi: "बंद", en: "Closed", statuses: ["closed", "cancelled"] },
];

function Audit({ id, onClose }: { id: string; onClose: () => void }) {
  const { both } = useLanguage();
  const ref = useRefData();
  const d = useLoad(() => api.caseDetail(id), `audit-${id}`);
  const users = useLoad(() => api.demoUsers(), "users");
  const who = (actor: string) => users.data?.find((u) => u.id === actor);
  return (
    <div role="dialog" aria-modal="true" aria-label={both("मामले का रिकॉर्ड", "Case audit trail")} style={{ position: "fixed", inset: 0, zIndex: 20, display: "flex", justifyContent: "flex-end" }}>
      <div className="scrim" onClick={onClose} />
      <aside className="sa-card" data-testid="audit" style={{ position: "relative", width: "min(480px, 100%)", height: "100%", borderRadius: 0, overflowY: "auto", gap: 16, padding: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 className="d-h2"><Bi hi="मामले का रिकॉर्ड" en="Audit trail" /></h2>
          <button type="button" className="sa-iconbtn" onClick={onClose} aria-label={both("बंद करें", "Close")}><Icon name="close" /></button>
        </div>
        {!d.data && (d.loading ? <Loading /> : <ErrorBox error={d.error} onRetry={d.reload} />)}
        {d.data && (
          <>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
              <span className="d-label"><DrugName d={ref.drug(d.data.drug_id)} id={d.data.drug_id} /> · <FacilityName f={ref.facility(d.data.facility_id)} id={d.data.facility_id} /></span>
              <CaseStatusChip status={d.data.status} />
            </div>
            <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column" }}>
              {d.data.events.map((e) => {
                const u = who(e.actor_id);
                const s = CASE_STATUS[e.to_status as CaseStatus];
                const w = when(e.at);
                return (
                  <li key={e.id} className="ev" data-testid="audit-event" style={{ display: "flex", gap: 12, padding: "12px 0", boxShadow: "inset 0 -1px 0 var(--line)" }}>
                    <span className="sa-avatar sa-avatar--sm">{initials(u?.name ?? e.actor_id)}</span>
                    <span style={{ flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
                      <span className="d-label">{s ? <Bi inline hi={s.hi} en={s.en} /> : e.to_status}</span>
                      <span className="d-caption">{u ? `${u.name} · ${u.role}` : e.actor_id}{e.note ? ` — ${e.note}` : ""}</span>
                    </span>
                    <span className="d-caption num" style={{ whiteSpace: "nowrap" }}><Bi hi={w.hi} en={w.en} /></span>
                  </li>
                );
              })}
            </ol>
          </>
        )}
      </aside>
    </div>
  );
}

export default function CaseBoard() {
  const ref = useRefData();
  const now = useNow();
  const who = usePatientNames();
  const cases = useLoad(() => api.cases(), "all-cases");
  const [open, setOpen] = useState<string | null>(null);
  const all = cases.data ?? [];
  return (
    <WebShell title={{ hi: "मामले", en: "Cases" }}>
      <h1 className="d-h1 hd"><Bi hi="मामलों का बोर्ड" en="Case board" /></h1>
      {cases.loading && !cases.data && <Loading />}
      {cases.error ? <ErrorBox error={cases.error} onRetry={cases.reload} /> : null}
      {cases.data && all.length === 0 && <Empty hi="कोई मामला नहीं" en="No cases yet" />}
      {all.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(6, minmax(180px, 1fr))", gap: 12, overflowX: "auto", alignItems: "start" }}>
          {COLUMNS.map((col) => {
            const items = all.filter((c) => col.statuses.includes(c.status));
            return (
              <section key={col.en} className="col" style={{ display: "flex", flexDirection: "column", gap: 8, minWidth: 180 }}>
                <div className="colh" style={{ display: "flex", justifyContent: "space-between" }}><span className="d-label"><Bi hi={col.hi} en={col.en} /></span><span className="sa-count">{items.length}</span></div>
                {items.map((c) => {
                  const a = age(c.created_at, now);
                  return (
                    <button key={c.id} type="button" className="kc sa-card" data-testid={`board-${c.id}`} onClick={() => setOpen(c.id)} style={{ gap: 6, textAlign: "left", cursor: "pointer", border: 0 }}>
                      <span className="kc-top" style={{ display: "flex", justifyContent: "space-between", gap: 6 }}><span className="sa-avatar sa-avatar--sm">{initials(who(c.patient_id).initials)}</span><CaseStatusChip status={c.status} /></span>
                      <span className="d-label"><Bi inline hi={who(c.patient_id).hi} en={who(c.patient_id).en} /></span>
                      <span className="kc-med d-caption"><DrugName d={ref.drug(c.drug_id)} id={c.drug_id} /></span>
                      <span className="kc-phc d-caption"><FacilityName f={ref.facility(c.facility_id)} id={c.facility_id} /></span>
                      <span className="sa-age"><Bi inline hi={a.hi} en={a.en} /></span>
                    </button>
                  );
                })}
              </section>
            );
          })}
        </div>
      )}
      {open && <Audit id={open} onClose={() => setOpen(null)} />}
    </WebShell>
  );
}
