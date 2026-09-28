"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { api, OverviewRow, Transfer } from "@/lib/api";
import { useLoad, useRefData } from "@/lib/hooks";
import { WebShell } from "@/components/shells";
import { DraftButton, WARN, pending, useDistrict } from "@/components/district";
import { Bi, DrugName, ErrorBox, FacilityName, Icon, Loading, Status, age, hiName, useNow, when } from "@/components/ui";
import { useLanguage } from "@/i18n/LanguageProvider";

type SortKey = "centre" | "on_hand" | "age" | "need" | "forecast" | "days" | "warning" | "cases";
const WARN_RANK: Record<string, number> = { critical: 0, low: 1, ok: 2 };

export default function DistrictOverview() {
  const district = useDistrict();
  const ref = useRefData();
  const now = useNow();
  const { both } = useLanguage();
  const data = useLoad(async () => {
    if (!district) return pending<never>();
    const [rows, cases, transfers] = await Promise.all([
      api.overview(district),
      api.cases(),
      api.transfers({ status: "draft" }).catch(() => [] as Transfer[]),
    ]);
    return { rows, cases, transfers };
  }, `ov-${district}`);

  const [centre, setCentre] = useState("all");
  const [med, setMed] = useState("all");
  const [warnOnly, setWarnOnly] = useState(false);
  const [sort, setSort] = useState<{ k: SortKey; asc: boolean }>({ k: "days", asc: true });

  const rows = useMemo(() => {
    const val = (r: OverviewRow): number | string => {
      switch (sort.k) {
        case "centre": return ref.facility(r.facility_id)?.name ?? r.facility_id;
        case "on_hand": return r.on_hand;
        case "age": return -new Date(r.recorded_at).getTime();
        case "need": return r.cohort_need;
        case "forecast": return r.dispensing_forecast;
        case "days": return r.days_left;
        case "warning": return WARN_RANK[r.warning ?? "ok"] ?? 3;
        case "cases": return r.open_cases;
      }
    };
    return (data.data?.rows ?? [])
      .filter((r) => ref.facility(r.facility_id)?.type !== "district_store")
      .filter((r) => (centre === "all" || r.facility_id === centre) && (med === "all" || r.drug_id === med) && (!warnOnly || (r.warning && r.warning !== "ok")))
      .sort((a, b) => {
        const x = val(a), y = val(b);
        const c = typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y));
        return sort.asc ? c : -c;
      });
  }, [data.data, centre, med, warnOnly, sort, ref]);

  const isStore = (id: string) => ref.facility(id)?.type === "district_store";
  const all = (data.data?.rows ?? []).filter((r) => !isStore(r.facility_id));
  const warnings = all.filter((r) => r.warning && r.warning !== "ok").length;
  const openCases = (data.data?.cases ?? []).filter((c) => c.status !== "closed" && c.status !== "cancelled");
  const needAction = openCases.filter((c) => (c.status === "verified" && c.verification.result === "confirmed_stockout") || c.status === "transfer_drafted");
  const drafts = data.data?.transfers ?? [];

  const th = (k: SortKey, hi: string, en: string, num?: boolean) => (
    <button type="button" className={`dt-th${num ? " is-num" : ""}${sort.k === k ? " is-sorted" : ""}`} role="columnheader"
      aria-sort={sort.k === k ? (sort.asc ? "ascending" : "descending") : "none"} onClick={() => setSort((s) => ({ k, asc: s.k === k ? !s.asc : true }))}>
      <Bi hi={hi} en={en} />{sort.k === k && <Icon name="chevron-down" size={16} style={{ transform: sort.asc ? "rotate(180deg)" : undefined }} />}
    </button>
  );

  return (
    <WebShell title={{ hi: `अवलोकन · ${district}`, en: `Overview · ${district}` }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 16, flexWrap: "wrap" }}>
        <div>
          <h1 className="d-h1 hd"><Bi hi="ज़िला स्टॉक और चेतावनी" en="District stock & warnings" /></h1>
          <p className="d-body-sm muted"><Bi hi="हर PHC × हर दवा · दिन = मरीज़ों की ज़रूरत के हिसाब से" en="Every PHC × medicine · days left are counted at patients' need, not past dispensing" /></p>
        </div>
        <Link className="sa-btn sa-btn--web sa-btn--outline" href="/district/evaluation"><Icon name="suggest" size={20} /><Bi hi="चेतावनी कितनी सही है?" en="How well does the warning work?" /></Link>
      </div>

      {data.loading && !data.data && <Loading />}
      {data.error ? <ErrorBox error={data.error} onRetry={data.reload} /> : null}

      {data.data && (
        <div className="grid-kpi">
          <div className="sa-card sa-card--web kpi"><span className="d-label"><Bi hi="खुले मामले" en="Open cases" /></span><span className="d-kpi">{openCases.length}</span></div>
          <div className="sa-card sa-card--web kpi"><span className="d-label"><Bi hi="शुरुआती चेतावनी" en="Early warnings" /></span><span className="d-kpi" style={{ color: warnings ? "var(--status-out)" : undefined }}>{warnings}</span><span className="d-caption"><Bi inline hi="14 दिन में ख़त्म" en="run out within 14 days" /></span></div>
          <div className="sa-card sa-card--web kpi"><span className="d-label"><Bi hi="मंज़ूरी बाकी" en="Awaiting your approval" /></span><span className="d-kpi">{drafts.length}</span><span className="d-caption"><Bi inline hi="AI मसौदे" en="AI transfer drafts" /></span></div>
        </div>
      )}

      {(needAction.length > 0 || drafts.length > 0) && (
        <section className="sa-card sa-card--web" style={{ gap: 12 }} data-testid="needs-action">
          <h2 className="d-h3"><Bi inline hi="आपका काम" en="Needs your action" /></h2>
          {needAction.filter((c) => c.status === "verified").map((c) => (
            <div key={c.id} style={{ display: "flex", gap: 16, alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", padding: "8px 0", boxShadow: "inset 0 -1px 0 var(--line)" }}>
              <span style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <span className="d-label"><DrugName d={ref.drug(c.drug_id)} id={c.drug_id} /> · <FacilityName f={ref.facility(c.facility_id)} id={c.facility_id} /></span>
                <span className="d-caption"><Bi inline hi={`फ़ार्मासिस्ट ने स्टॉक ख़त्म पक्का किया · ${age(c.verification.at ?? c.updated_at, now).hi}`} en={`Pharmacist confirmed out of stock · ${age(c.verification.at ?? c.updated_at, now).en}`} /></span>
              </span>
              <DraftButton c={c} onDone={data.reload} />
            </div>
          ))}
          {drafts.map((t) => (
            <Link key={t.id} href={`/district/transfers/${t.id}`} className="sa-row" style={{ minHeight: 60 }}>
              <span className="sa-row-ic"><Icon name="transfer" /></span>
              <span className="sa-row-main"><DrugName d={ref.drug(t.drug_id)} id={t.drug_id} /> · <span className="num">{t.quantity}</span> · <FacilityName f={ref.facility(t.from_facility_id)} id={t.from_facility_id} /> → <FacilityName f={ref.facility(t.to_facility_id)} id={t.to_facility_id} /></span>
              <Status tone="wait" icon="suggest" hi="मंज़ूरी बाकी" en="Review" />
            </Link>
          ))}
        </section>
      )}

      {data.data && (
        <>
          <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <label className="sa-input sa-input--web" style={{ width: 220 }}>
              <select aria-label={both("केंद्र", "Centre")} value={centre} onChange={(e) => setCentre(e.target.value)} style={{ border: 0, background: "transparent", width: "100%" }}>
                <option value="all">{both("सभी केंद्र", "All centres")}</option>
                {ref.data?.facilities.filter((f) => f.type !== "district_store").map((f) => <option key={f.id} value={f.id}>{f.name} · {hiName(f, "facility")}</option>)}
              </select>
            </label>
            <div role="group" aria-label={both("दवा", "Medicine")} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button type="button" className="sa-chip" aria-pressed={med === "all"} onClick={() => setMed("all")}><Bi inline hi="सभी" en="All" /></button>
              {ref.data?.drugs.map((d) => (
                <button key={d.id} type="button" className="sa-chip" aria-pressed={med === d.id} onClick={() => setMed(d.id)}><Bi inline hi={hiName(d, "drug")} en={d.name} /></button>
              ))}
            </div>
            <button type="button" className="sa-chip" aria-pressed={warnOnly} onClick={() => setWarnOnly((w) => !w)}><Bi inline hi="सिर्फ़ चेतावनी" en="Warnings only" /><span className="sa-count">{warnings}</span></button>
          </div>

          <section className="table-scroll">
            <div className="dt" role="table" aria-label={both("केंद्र और दवा के हिसाब से स्टॉक", "Stock by PHC and medicine")} data-testid="overview-table">
              <div className="dt-row dt-head" role="row">
                {th("centre", "केंद्र · दवा", "Centre · medicine")}
                {th("on_hand", "स्टॉक", "On hand", true)}
                {th("age", "कब का डेटा", "Data age")}
                {th("need", "ज़रूरत · 30 दिन", "Patients' need", true)}
                {th("forecast", "वितरण अनुमान", "Dispensing forecast", true)}
                {th("days", "दिन बचे", "Days left", true)}
                {th("warning", "चेतावनी", "Warning")}
                {th("cases", "मामले", "Cases", true)}
              </div>
              <div className="dt-body" role="rowgroup">
                {rows.map((r) => {
                  const w = WARN[r.warning ?? "ok"] ?? WARN.ok;
                  const a = age(r.recorded_at, now);
                  return (
                    <Link key={`${r.facility_id}-${r.drug_id}`} role="row" href={`/district/facility/${r.facility_id}?drug=${r.drug_id}`}
                      className={`dt-row${r.warning === "critical" ? " is-out" : ""}`} data-testid={`row-${r.facility_id}-${r.drug_id}`}>
                      <span className="dt-td" role="cell"><span className="dt-2"><FacilityName f={ref.facility(r.facility_id)} id={r.facility_id} /><span className="d-caption"><DrugName d={ref.drug(r.drug_id)} id={r.drug_id} /></span></span></span>
                      <span className="dt-td is-num num" role="cell">{Math.round(r.on_hand)}</span>
                      <span className="dt-td" role="cell"><span className="sa-age" title={when(r.recorded_at).en}><span className="sa-age-dot" style={{ background: `var(--status-${a.tone}-solid)` }} /><Bi inline hi={a.hi} en={a.en} /></span></span>
                      <span className="dt-td is-num num" role="cell">{Math.round(r.cohort_need)}</span>
                      <span className="dt-td is-num num" role="cell">{Math.round(r.dispensing_forecast)}</span>
                      <span className="dt-td is-num num" role="cell" style={{ fontWeight: 600 }}>{r.days_left >= 999 ? "—" : r.days_left.toFixed(r.days_left < 10 ? 1 : 0)}</span>
                      <span className="dt-td" role="cell"><Status tone={w.tone} hi={w.hi} en={w.en} /></span>
                      <span className="dt-td is-num num" role="cell">{r.open_cases}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
            <p className="d-caption" style={{ marginTop: 8 }}>
              <Bi inline hi="ज़रूरत = चालू पर्चियाँ × रोज़ की खुराक (30 दिन)। अनुमान = पिछला वितरण क्या बताता है। दिन बचे = स्टॉक ÷ दोनों में बड़ा।" en="Need = active prescriptions × daily dose (30 days). Forecast = what past dispensing predicts. Days left = stock ÷ the larger of the two." />
            </p>
          </section>
        </>
      )}
    </WebShell>
  );
}
