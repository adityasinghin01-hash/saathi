"use client";

import { useState } from "react";
import Link from "next/link";
import { api, Patient } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useLoad, useRefData } from "@/lib/hooks";
import { PhoneShell } from "@/components/shells";
import { Bi, CASE_STATUS, DemoBadge, Empty, ErrorBox, Icon, Loading, Status, Tone, hiName, initials } from "@/components/ui";

type Filter = "all" | "open" | "ok";

function tone(p: Patient): { tone: Tone; hi: string; en: string; icon?: string } {
  const c = p.open_case;
  if (!c) return { tone: "ok", hi: "ठीक", en: "OK" };
  const s = CASE_STATUS[c.status];
  return { tone: s.tone, hi: s.hi, en: s.en, icon: s.icon };
}

export default function AshaHome() {
  const { user } = useAuth();
  const ref = useRefData();
  const patients = useLoad(() => api.patients(), "asha-patients");
  const [f, setF] = useState<Filter>("all");
  const all = patients.data ?? [];
  const shown = all.filter((p) => f === "all" || (f === "open" ? p.open_case : !p.open_case));
  const chips: { k: Filter; hi: string; en: string; n: number }[] = [
    { k: "all", hi: "सभी", en: "All", n: all.length },
    { k: "open", hi: "खुली शिकायत", en: "Open report", n: all.filter((p) => p.open_case).length },
    { k: "ok", hi: "ठीक", en: "OK", n: all.filter((p) => !p.open_case).length },
  ];
  const first = hiName(user ?? undefined).split(" ")[0];

  return (
    <PhoneShell title={{ hi: "मेरे मरीज़", en: "My patients" }}
      foot={<Link className="sa-btn sa-btn--hero" href="/patient/report" data-testid="report-for"><Icon name="mic" size={28} /><Bi hi="मरीज़ के लिए रिपोर्ट करें" en="Report for a patient" /></Link>}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <h1 className="m-title hd"><Bi hi={`नमस्ते, ${first} दीदी`} en={`Hello, ${(user?.name ?? "").split(" ")[0]}`} /></h1>
          {user && <span className="m-caption"><Bi inline hi={`${hiName(ref.facility(user.facility_id), "facility")} क्षेत्र`} en={`${ref.facility(user.facility_id)?.name ?? ""} area`} /></span>}
        </div>
        <DemoBadge />
      </div>
      <div role="group" aria-label="Filter · छाँटें" style={{ display: "flex", gap: 8, overflowX: "auto" }}>
        {chips.map((c) => (
          <button key={c.k} type="button" className="sa-chip" aria-pressed={f === c.k} onClick={() => setF(c.k)} style={{ flex: "none" }}>
            <Bi inline hi={c.hi} en={c.en} /><span className="sa-count">{c.n}</span>
          </button>
        ))}
      </div>
      {patients.loading && !patients.data && <Loading />}
      {patients.error ? <ErrorBox error={patients.error} onRetry={patients.reload} /> : null}
      {patients.data && shown.length === 0 && <Empty hi="कोई मरीज़ नहीं" en="No patients here" />}
      <div className="sa-rows">
        {shown.map((p) => {
          const t = tone(p);
          const href = p.open_case ? `/patient/cases/${p.open_case.id}` : `/patient/report?patient=${p.id}`;
          return (
            <Link key={p.id} className="pt" href={href} data-testid={`patient-${p.id}`}>
              <span className="sa-avatar sa-avatar--sunk">{initials(p.name)}</span>
              <span className="pt-main">
                <span className="pt-name"><Bi hi={`${hiName(p)}, ${p.age}`} en={`${p.name}, ${p.age}`} /></span>
                <span className="m-caption" style={{ fontSize: 13, lineHeight: "18px" }}>
                  {p.prescriptions.filter((r) => r.active).map((r) => { const d = ref.drug(r.drug_id); return d ? `${d.name} ${d.strength}` : r.drug_id; }).join(" · ")}
                </span>
              </span>
              <Status tone={t.tone} hi={t.hi} en={t.en} icon={t.icon} />
            </Link>
          );
        })}
      </div>
    </PhoneShell>
  );
}
