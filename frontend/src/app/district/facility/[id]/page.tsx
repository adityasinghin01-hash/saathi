"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { api, Series } from "@/lib/api";
import { useLoad, usePatientNames, useRefData } from "@/lib/hooks";
import { WebShell } from "@/components/shells";
import { DraftButton, WARN, pending, useDistrict } from "@/components/district";
import { Bi, CaseStatusChip, DataAge, DrugName, ErrorBox, FacilityName, Icon, Loading, Status, hiName, useNow, when } from "@/components/ui";

/** Daily units: dispensed (bars), patients' need/day and forecast/day (lines); stock-out days shaded as hidden demand. */
function DemandChart({ s }: { s: Series }) {
  const W = 760, H = 240, P = { l: 44, r: 12, t: 12, b: 28 };
  const days = s.days;
  const maxY = Math.max(1, s.cohort_need_daily, s.dispensing_forecast_daily, ...days.map((d) => d.dispensed)) * 1.15;
  const x = (i: number) => P.l + (i * (W - P.l - P.r)) / Math.max(1, days.length);
  const bw = Math.max(2, (W - P.l - P.r) / Math.max(1, days.length) - 2);
  const y = (v: number) => H - P.b - (v / maxY) * (H - P.t - P.b);
  const ticks = [0, maxY / 2, maxY].map((v) => Math.round(v));
  return (
    <figure style={{ margin: 0 }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Daily dispensing vs patients' need · रोज़ का वितरण बनाम ज़रूरत" className="sa-chart">
        {ticks.map((t) => <g key={t}><line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} stroke="var(--chart-grid)" /><text x={P.l - 6} y={y(t) + 4} textAnchor="end" fontSize="11" fill="var(--ink-muted)">{t}</text></g>)}
        {days.map((d, i) => d.stockout && <rect key={`s${i}`} x={x(i)} y={P.t} width={bw + 2} height={H - P.t - P.b} fill="var(--status-out-bg)" />)}
        {days.map((d, i) => <rect key={i} x={x(i) + 1} y={y(d.dispensed)} width={bw} height={Math.max(0, H - P.b - y(d.dispensed))} fill="var(--chart-stock)" rx="1" />)}
        <line x1={P.l} x2={W - P.r} y1={y(s.cohort_need_daily)} y2={y(s.cohort_need_daily)} stroke="var(--chart-need)" strokeWidth="2.5" />
        <line x1={P.l} x2={W - P.r} y1={y(s.dispensing_forecast_daily)} y2={y(s.dispensing_forecast_daily)} stroke="var(--chart-3)" strokeWidth="2" strokeDasharray="6 5" />
        <text x={P.l} y={H - 8} fontSize="11" fill="var(--ink-muted)">{days[0]?.date}</text>
        <text x={W - P.r} y={H - 8} fontSize="11" fill="var(--ink-muted)" textAnchor="end">{days.at(-1)?.date}</text>
      </svg>
      <figcaption className="sa-legend" style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 8 }}>
        <span className="d-caption"><span style={{ display: "inline-block", width: 12, height: 12, background: "var(--chart-stock)", borderRadius: 2, marginRight: 6 }} /><Bi inline hi="रोज़ दी गई गोलियाँ" en="Tablets dispensed per day" /></span>
        <span className="d-caption"><span style={{ display: "inline-block", width: 16, height: 3, background: "var(--chart-need)", marginRight: 6, verticalAlign: "middle" }} /><Bi inline hi="मरीज़ों की रोज़ की ज़रूरत" en="Patients' need per day" /></span>
        <span className="d-caption"><span style={{ display: "inline-block", width: 16, height: 0, borderTop: "2px dashed var(--chart-3)", marginRight: 6, verticalAlign: "middle" }} /><Bi inline hi="वितरण का अनुमान" en="Dispensing forecast" /></span>
        <span className="d-caption"><span style={{ display: "inline-block", width: 12, height: 12, background: "var(--status-out-bg)", marginRight: 6 }} /><Bi inline hi="छिपी माँग — मरीज़ आए, दवा नहीं थी" en="Hidden demand — patients came, no medicine" /></span>
      </figcaption>
    </figure>
  );
}

function FacilityDetail() {
  const { id } = useParams<{ id: string }>();
  const drugId = useSearchParams().get("drug") ?? "metformin";
  const district = useDistrict();
  const ref = useRefData();
  const now = useNow();
  const who = usePatientNames();
  const data = useLoad(async () => {
    if (!district) return pending<never>();
    const [rows, cases, series] = await Promise.all([
      api.overview(district),
      api.cases({ facility_id: id }),
      api.series(id, drugId).catch(() => null),
    ]);
    return { row: rows.find((r) => r.facility_id === id && r.drug_id === drugId), cases: cases.filter((c) => c.drug_id === drugId), series };
  }, `fac-${id}-${drugId}-${district}`);

  const f = ref.facility(id), d = ref.drug(drugId);
  const row = data.data?.row;
  const w = WARN[row?.warning ?? "ok"] ?? WARN.ok;
  const open = (data.data?.cases ?? []).filter((c) => c.status !== "closed" && c.status !== "cancelled");

  return (
    <WebShell title={{ hi: `${hiName(f, "facility")} × ${hiName(d, "drug")}`, en: `${f?.name ?? id} × ${d?.name ?? drugId}` }}>
      <nav aria-label="Breadcrumb · रास्ता" className="d-caption"><Link className="lnk" href="/district"><Bi inline hi="अवलोकन" en="Overview" /></Link> / <FacilityName f={f} id={id} /> × <DrugName d={d} id={drugId} /></nav>
      {data.loading && !data.data && <Loading />}
      {data.error ? <ErrorBox error={data.error} onRetry={data.reload} /> : null}
      {row && (
        <div className="grid-kpi">
          <div className="sa-card sa-card--web kpi"><span className="d-label"><Bi hi="स्टॉक" en="On hand" /></span><span className="d-kpi">{Math.round(row.on_hand)}</span><DataAge iso={row.recorded_at} now={now} /></div>
          <div className="sa-card sa-card--web kpi"><span className="d-label"><Bi hi="ज़रूरत · 30 दिन" en="Patients' need · 30 days" /></span><span className="d-kpi">{Math.round(row.cohort_need)}</span></div>
          <div className="sa-card sa-card--web kpi"><span className="d-label"><Bi hi="वितरण अनुमान · 30 दिन" en="Dispensing forecast · 30 days" /></span><span className="d-kpi">{Math.round(row.dispensing_forecast)}</span></div>
          <div className="sa-card sa-card--web kpi"><span className="d-label"><Bi hi="दिन बचे" en="Days left" /></span><span className="d-kpi" style={{ color: `var(--status-${w.tone})` }}>{row.days_left >= 999 ? "—" : row.days_left.toFixed(1)}</span><Status tone={w.tone} hi={w.hi} en={w.en} /></div>
        </div>
      )}
      <div className="split">
        <section className="sa-card sa-card--web" style={{ gap: 12 }}>
          <h2 className="d-h3"><Bi inline hi="पिछले 60 दिन: ज़रूरत बनाम वितरण" en="Last 60 days: need vs dispensing" /></h2>
          {data.data?.series ? <DemandChart s={data.data.series} /> : data.data && <p className="d-caption"><Bi inline hi="रोज़ का डेटा अभी उपलब्ध नहीं" en="Daily history not available yet" /></p>}
          <p className="d-caption"><Bi hi="स्टॉक ख़त्म वाले दिनों में वितरण शून्य दिखता है, पर माँग शून्य नहीं थी — इसलिए हम मरीज़ों की पर्चियों से ज़रूरत गिनते हैं।" en="On stock-out days dispensing reads zero, but demand wasn't zero — that's why need is counted from patients' prescriptions." /></p>
        </section>
        <section className="sa-card sa-card--web" style={{ gap: 12 }}>
          <h2 className="d-h3"><Bi inline hi="खुले मामले" en="Open cases" /> <span className="sa-count">{open.length}</span></h2>
          {open.length === 0 && data.data && <p className="d-caption"><Bi inline hi="कोई खुला मामला नहीं" en="No open cases" /></p>}
          {open.map((c) => (
            <div key={c.id} style={{ display: "flex", flexDirection: "column", gap: 8, paddingBottom: 12, boxShadow: "inset 0 -1px 0 var(--line)" }}>
              <span style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                <span className="d-label"><Bi inline hi={who(c.patient_id).hi} en={who(c.patient_id).en} /></span><CaseStatusChip status={c.status} />
              </span>
              <span className="d-caption"><Bi inline hi={`माँगी ${c.requested_qty} · ${when(c.created_at).hi}`} en={`asked ${c.requested_qty} · ${when(c.created_at).en}`} /></span>
              {(c.status === "verified" && c.verification.result === "confirmed_stockout") || c.status === "transfer_drafted" ? <DraftButton c={c} onDone={data.reload} /> : null}
              {c.transfer_id && c.status !== "transfer_drafted" && <Link className="lnk" href={`/district/transfers/${c.transfer_id}`}><Icon name="transfer" size={16} /> <Bi inline hi="ट्रांसफ़र देखें" en="View transfer" /></Link>}
            </div>
          ))}
        </section>
      </div>
    </WebShell>
  );
}

export default function FacilityPage() {
  return (
    <Suspense fallback={<div className="center-page"><Loading /></div>}>
      <FacilityDetail />
    </Suspense>
  );
}
