"use client";

import Link from "next/link";
import { api, Case, Transfer } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useLoad, usePatientNames, useRefData } from "@/lib/hooks";
import { PhoneShell } from "@/components/shells";
import { Bi, CaseStatusChip, DemoBadge, DrugName, Empty, ErrorBox, FacilityName, Icon, Loading, age, hiName, initials, useNow } from "@/components/ui";

export default function PharmacistHome() {
  const { user } = useAuth();
  const ref = useRefData();
  const now = useNow();
  const who = usePatientNames();
  const fid = user?.facility_id ?? "";
  const data = useLoad(async () => {
    const [cases, transfers] = await Promise.all([
      api.cases({ facility_id: fid }),
      api.transfers({ facility_id: fid }).catch(() => [] as Transfer[]),
    ]);
    return { cases, transfers };
  }, `ph-${fid}`);

  const cases = data.data?.cases ?? [];
  const toVerify = cases.filter((c) => c.status === "reported");
  const toGive = cases.filter((c) => c.status === "received" || c.status === "partially_supplied" || (c.status === "verified" && c.verification.result === "stock_available"));
  const incoming = (data.data?.transfers ?? []).filter((t) => t.to_facility_id === fid && (t.status === "dispatched" || t.status === "approved"));
  // Transfers are also reachable through cases, so the screen still works if /transfers is missing.
  const viaCases = cases.filter((c) => c.status === "dispatched" && c.transfer_id && !incoming.some((t) => t.id === c.transfer_id));
  const first = hiName(user ?? undefined).split(" ")[0];

  const row = (c: Case, href: string) => {
    const a = age(c.created_at, now);
    return (
      <Link key={c.id} className="sa-row" href={href} data-testid={`case-row-${c.id}`} style={{ minHeight: 76 }}>
        <span className="sa-avatar sa-avatar--sunk">{initials(who(c.patient_id).initials)}</span>
        <span className="sa-row-main" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <span style={{ font: "600 16px/22px var(--font-sans)" }}><DrugName d={ref.drug(c.drug_id)} id={c.drug_id} /></span>
          <span className="m-caption" style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <Icon name={c.channel === "voice" ? "mic" : "edit"} size={16} />
            <Bi inline hi={`${who(c.patient_id).hi} · ${a.hi}`} en={`${who(c.patient_id).en} · ${a.en}`} />
          </span>
        </span>
        <CaseStatusChip status={c.status} />
      </Link>
    );
  };

  return (
    <PhoneShell title={{ hi: "घर", en: "Home" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <h1 className="m-title hd"><Bi hi={`नमस्ते, ${first}`} en={`Hello, ${(user?.name ?? "").split(" ")[0]}`} /></h1>
          {user && <span className="m-caption"><FacilityName f={ref.facility(fid)} id={fid} /> · <Bi inline hi="फ़ार्मासिस्ट" en="Pharmacist" /></span>}
        </div>
        <DemoBadge />
      </div>

      <div className="grid-2">
        <div className="sa-card" style={{ gap: 8 }}>
          <span style={{ width: 40, height: 40, borderRadius: 12, background: "var(--clay-100)", color: "var(--clay-ink)", display: "grid", placeItems: "center" }}><Icon name="cases" size={20} /></span>
          <span className="m-number" data-testid="count-verify">{toVerify.length}</span>
          <span style={{ font: "600 15px/22px var(--font-sans)" }}><Bi hi="जाँच बाकी" en="To verify" /></span>
        </div>
        <div className="sa-card" style={{ gap: 8 }}>
          <span style={{ width: 40, height: 40, borderRadius: 12, background: "var(--marigold-100)", display: "grid", placeItems: "center" }}><Icon name="truck" size={20} /></span>
          <span className="m-number">{incoming.length + viaCases.length}</span>
          <span style={{ font: "600 15px/22px var(--font-sans)" }}><Bi hi="स्टॉक आ रहा" en="Arriving" /></span>
        </div>
      </div>

      {data.loading && !data.data && <Loading />}
      {data.error ? <ErrorBox error={data.error} onRetry={data.reload} /> : null}

      {(incoming.length > 0 || viaCases.length > 0) && (
        <section style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <h2 className="m-heading" style={{ fontSize: 18 }}><Bi inline hi="आ रहा स्टॉक" en="Incoming stock" /></h2>
          <div className="sa-rows">
            {incoming.map((t) => (
              <Link key={t.id} className="sa-row" href={`/pharmacist/transfer/${t.id}`} data-testid={`incoming-${t.id}`} style={{ minHeight: 72 }}>
                <span className="sa-row-ic"><Icon name="truck" /></span>
                <span className="sa-row-main" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  <span style={{ font: "600 16px/22px var(--font-sans)" }}><DrugName d={ref.drug(t.drug_id)} id={t.drug_id} /> · <span className="num">{t.quantity}</span></span>
                  <span className="m-caption"><Bi inline hi={`${hiName(ref.facility(t.from_facility_id), "facility")} से`} en={`from ${ref.facility(t.from_facility_id)?.name ?? t.from_facility_id}`} /></span>
                </span>
                <Icon name="chevron-right" />
              </Link>
            ))}
            {viaCases.map((c) => (
              <Link key={c.id} className="sa-row" href={`/pharmacist/transfer/${c.transfer_id}`} data-testid={`incoming-${c.transfer_id}`} style={{ minHeight: 72 }}>
                <span className="sa-row-ic"><Icon name="truck" /></span>
                <span className="sa-row-main"><DrugName d={ref.drug(c.drug_id)} id={c.drug_id} /></span>
                <Icon name="chevron-right" />
              </Link>
            ))}
          </div>
        </section>
      )}

      {toGive.length > 0 && (
        <section style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <h2 className="m-heading" style={{ fontSize: 18 }}><Bi inline hi="मरीज़ को दें" en="Ready to hand over" /></h2>
          <div className="sa-rows">{toGive.map((c) => row(c, `/pharmacist/give/${c.id}`))}</div>
        </section>
      )}

      <section style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <h2 className="m-heading" style={{ fontSize: 18 }}><Bi inline hi="जाँच की कतार" en="Verify queue" /></h2>
        {data.data && toVerify.length === 0 && <Empty hi="जाँचने को कुछ नहीं" en="Nothing to verify" art="shelf" />}
        <div className="sa-rows">{toVerify.map((c) => row(c, `/pharmacist/verify/${c.id}`))}</div>
      </section>
    </PhoneShell>
  );
}
