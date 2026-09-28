"use client";

import { api } from "@/lib/api";
import { useLoad } from "@/lib/hooks";
import { WebShell } from "@/components/shells";
import { Bi, ErrorBox, Icon, Loading } from "@/components/ui";

interface MethodResult { mae_daily: number; false_alert_rate: number; unmet_patient_days: number; overstock_units: number; stockout_days: number; alert_lead_days: number }
interface Summary {
  forecast: { repetitions: number; horizon_days: number; scenarios: Record<string, { methods: Record<string, MethodResult> }> };
  extraction: { corpus: string; limitations?: string[]; live?: { samples: number; successful_calls: number; failed_calls: number; field_accuracy: Record<string, number>; latency_ms_mean: number; models_answered?: Record<string, number> } };
}

const SCEN: Record<string, { hi: string; en: string }> = {
  baseline: { hi: "सामान्य", en: "Normal month" },
  enrolment_gap: { hi: "कई मरीज़ दर्ज नहीं", en: "Many patients not enrolled" },
  stale_prescriptions: { hi: "पुरानी पर्चियाँ", en: "Out-of-date prescriptions" },
  false_reports: { hi: "झूठी शिकायतें", en: "False reports" },
  outside_purchases: { hi: "बाहर से ख़रीद", en: "Patients buy outside" },
  long_stockout: { hi: "लंबा स्टॉक-आउट", en: "Long stock-out" },
};
const FIELDS: Record<string, { hi: string; en: string }> = {
  medicine: { hi: "दवा", en: "Medicine" }, strength: { hi: "ताक़त", en: "Strength" }, date: { hi: "तारीख़", en: "Date" },
  requested_qty: { hi: "मात्रा", en: "Quantity" }, household_supply_days: { hi: "घर पर बची", en: "Left at home" }, negated: { hi: "'मिल गई' पहचाना", en: "Caught 'I did get it'" },
};

export default function EvaluationPage() {
  const s = useLoad(() => api.evaluation() as unknown as Promise<Summary>, "eval");
  const base = s.data?.forecast.scenarios.baseline?.methods;
  const old = base?.dispensing_only, ours = base?.prescription_only;
  const live = s.data?.extraction.live;

  return (
    <WebShell title={{ hi: "जाँच के नतीजे", en: "Evaluation" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 16, flexWrap: "wrap" }}>
        <div>
          <h1 className="d-h1 hd"><Bi hi="चेतावनी कितनी सही है?" en="How well does the warning work?" /></h1>
          <p className="d-body-sm muted"><Bi hi="हमारा ईमानदार परीक्षण — जहाँ जीते और जहाँ हारे, दोनों" en="Our honest test — where it wins and where it loses" /></p>
        </div>
        <span className="sa-demo" data-testid="sim-label"><Bi inline hi="नकली सिमुलेशन — असली मरीज़ नहीं" en="Synthetic simulation — not real patients" /></span>
      </div>
      {s.loading && !s.data && <Loading />}
      {s.error ? <ErrorBox error={s.error} onRetry={s.reload} /> : null}

      {old && ours && (
        <div className="grid-2">
          <section className="sa-card sa-card--web" style={{ gap: 10 }}>
            <span className="d-label"><Bi hi="बिना दवा के मरीज़-दिन" en="Patient-days without medicine" /></span>
            <span className="hero-n d-display num" style={{ display: "flex", gap: 12, alignItems: "baseline", flexWrap: "wrap" }}>
              <span style={{ color: "var(--ink-muted)", textDecoration: "line-through" }}>{Math.round(old.unmet_patient_days)}</span>
              <Icon name="chevron-right" />
              <span style={{ color: "var(--status-ok)" }}>{Math.round(ours.unmet_patient_days)}</span>
            </span>
            <p className="d-body"><Bi hi={`पुराना तरीक़ा (सिर्फ़ पिछला वितरण) बनाम मरीज़ों की पर्चियों से ज़रूरत — ${Math.round((1 - ours.unmet_patient_days / old.unmet_patient_days) * 100)}% कम`} en={`Old way (past dispensing only) vs need from patients' prescriptions — ${Math.round((1 - ours.unmet_patient_days / old.unmet_patient_days) * 100)}% fewer`} /></p>
          </section>
          <section className="sa-card sa-card--web" style={{ gap: 10 }}>
            <span className="d-label"><Bi hi="इसकी क़ीमत" en="The cost" /></span>
            <span className="hero-n d-display num" style={{ color: "var(--status-low)" }}>{Math.round(ours.false_alert_rate * 100)}%</span>
            <p className="d-body"><Bi hi={`परीक्षणों में झूठी चेतावनी · औसतन ${Math.round(ours.overstock_units)} गोलियाँ ज़्यादा स्टॉक में`} en={`of test runs raised a false alarm · about ${Math.round(ours.overstock_units)} extra tablets sitting on the shelf`} /></p>
            <p className="d-caption"><Bi hi="हम ज़्यादा मँगवाने को चुनते हैं, क्योंकि दवा न मिलना ज़्यादा महँगा है।" en="We accept over-ordering: a patient going without medicine costs more." /></p>
          </section>
        </div>
      )}

      {s.data && (
        <section className="sa-card sa-card--web" style={{ gap: 12 }}>
          <h2 className="d-h3"><Bi inline hi={`छह हालात, ${s.data.forecast.repetitions} बार दोहराया`} en={`Six situations, ${s.data.forecast.repetitions} runs each`} /></h2>
          <div className="table-scroll">
            <table className="sa-table" style={{ width: "100%" }}>
              <thead><tr>
                <th><Bi hi="हालात" en="Situation" /></th>
                <th className="num"><Bi hi="बिना दवा (पुराना)" en="Without medicine (old)" /></th>
                <th className="num"><Bi hi="बिना दवा (साथी)" en="Without medicine (Saathi)" /></th>
                <th className="num"><Bi hi="झूठी चेतावनी (साथी)" en="False alarms (Saathi)" /></th>
                <th className="num"><Bi hi="ज़्यादा स्टॉक (साथी)" en="Extra stock (Saathi)" /></th>
              </tr></thead>
              <tbody>
                {Object.entries(s.data.forecast.scenarios).map(([k, v]) => {
                  const o = v.methods.dispensing_only, n = v.methods.prescription_only;
                  return (
                    <tr key={k}>
                      <td><Bi hi={SCEN[k]?.hi ?? k} en={SCEN[k]?.en ?? k} /></td>
                      <td className="num">{o ? Math.round(o.unmet_patient_days) : "—"}</td>
                      <td className="num" style={{ fontWeight: 600 }}>{n ? Math.round(n.unmet_patient_days) : "—"}</td>
                      <td className="num">{n ? `${Math.round(n.false_alert_rate * 100)}%` : "—"}</td>
                      <td className="num">{n ? Math.round(n.overstock_units) : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="d-caption"><Bi inline hi="जहाँ मरीज़ दर्ज नहीं हैं (दूसरी पंक्ति), पर्चियों वाला तरीक़ा कुछ नहीं जोड़ता — इसे हम छिपाते नहीं।" en="Where patients aren't enrolled (row 2), the prescription method adds nothing — we don't hide that." /></p>
        </section>
      )}

      {live && (
        <section className="sa-card sa-card--web" style={{ gap: 12 }}>
          <h2 className="d-h3"><Bi inline hi="हिंदी में बोली शिकायत AI कितना समझता है" en="How well the AI reads a Hindi report" /></h2>
          <p className="d-body-sm"><Bi inline hi={`${live.samples} लिखे हुए वाक्य · ${live.successful_calls} सफल, ${live.failed_calls} में AI व्यस्त था (नियमों से बना मसौदा दिखा) · औसत ${(live.latency_ms_mean / 1000).toFixed(1)} सेकंड`} en={`${live.samples} written sentences · ${live.successful_calls} answered, ${live.failed_calls} got "AI busy" (rules fallback shown) · ${(live.latency_ms_mean / 1000).toFixed(1)} s average`} /></p>
          <div className="grid-kpi">
            {Object.entries(FIELDS).map(([k, lbl]) => live.field_accuracy[k] !== undefined && (
              <div key={k} className="kpi" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <span className="d-caption"><Bi inline hi={lbl.hi} en={lbl.en} /></span>
                <span className="d-kpi num">{Math.round(live.field_accuracy[k] * 100)}%</span>
              </div>
            ))}
          </div>
          <p className="d-caption"><Bi inline hi="सीमा: यह टाइप किए वाक्यों पर है, असली आवाज़ पर नहीं। हर AI जवाब इंसान जाँचता है।" en="Limit: this used typed sentences, not recorded speech. A person checks every AI answer." /></p>
        </section>
      )}
    </WebShell>
  );
}
