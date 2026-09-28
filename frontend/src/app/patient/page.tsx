"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useLoad, useRefData } from "@/lib/hooks";
import { PhoneShell } from "@/components/shells";
import { Bi, CaseStatusChip, DemoBadge, DrugName, ErrorBox, FacilityName, Icon, Loading } from "@/components/ui";

export default function PatientHome() {
  const { user } = useAuth();
  const ref = useRefData();
  const pid = user?.patient_id ?? "";
  const home = useLoad(async () => {
    const [patient, cases] = await Promise.all([api.patient(pid), api.cases()]);
    return { patient, cases };
  }, `home-${pid}`);
  const open = home.data?.cases.filter((c) => c.status !== "closed" && c.status !== "cancelled") ?? [];
  const first = (user?.name_hi ?? user?.name ?? "").split(/[ ,]/)[0];

  return (
    <PhoneShell title={{ hi: "घर", en: "Home" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <h1 className="m-title hd" style={{ ["--bi-2nd" as string]: "15px" }}>
          <Bi hi={`नमस्ते, ${first} जी`} en={`Hello, ${(user?.name ?? "").split(/[ ,]/)[0]}`} />
        </h1>
        <DemoBadge />
      </div>

      {home.loading && !home.data && <Loading />}
      {home.error ? <ErrorBox error={home.error} onRetry={home.reload} /> : null}

      {open.map((c) => (
        <Link key={c.id} href={`/patient/cases/${c.id}`} className="sa-card sa-card--action" data-testid="open-case" style={{ gap: 10 }}>
          <div className="sa-card-head">
            <span className="m-caption" style={{ fontWeight: 600 }}><Bi inline hi="मेरी शिकायत" en="My report" /></span>
            <CaseStatusChip status={c.status} />
          </div>
          <span className="m-heading" style={{ ["--bi-2nd" as string]: "14px" }}><DrugName d={ref.drug(c.drug_id)} id={c.drug_id} inline={false} /></span>
          <span className="sa-card-meta"><span className="sa-age"><Icon name="health-centre" size={16} /><FacilityName f={ref.facility(c.facility_id)} id={c.facility_id} /></span></span>
        </Link>
      ))}

      <Link className="sa-btn sa-btn--hero" href="/patient/report" data-testid="not-received">
        <Icon name="mic" size={28} />
        <Bi hi="दवा नहीं मिली" en="Medicine not received" />
      </Link>
      <p className="m-caption" style={{ textAlign: "center", marginTop: -8 }}><Bi inline hi="बस बोलकर बताइए — हम सुनेंगे" en="Just say it — we'll listen" /></p>

      {home.data && (
        <section style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <h2 className="m-heading" style={{ fontSize: 18 }}><Bi inline hi="मेरी दवाइयाँ" en="My medicines" /></h2>
          {home.data.patient.prescriptions.filter((p) => p.active).map((p) => (
            <section key={p.id} className="sa-card" style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
              <span style={{ width: 48, height: 48, borderRadius: 16, background: "var(--clay-100)", color: "var(--clay-ink)", display: "grid", placeItems: "center", flex: "none" }}><Icon name="medicines" /></span>
              <span style={{ flexGrow: 1, font: "600 17px/24px var(--font-sans)", ["--bi-2nd" as string]: "14px" }}>
                <DrugName d={ref.drug(p.drug_id)} id={p.drug_id} inline={false} />
                <span className="m-caption" style={{ display: "block" }}><Bi inline hi={`रोज़ ${p.dose_per_day} गोली`} en={`${p.dose_per_day} a day`} /></span>
              </span>
            </section>
          ))}
        </section>
      )}
    </PhoneShell>
  );
}
