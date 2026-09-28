"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useLoad, useRefData } from "@/lib/hooks";
import { PhoneShell } from "@/components/shells";
import { Bi, CaseStatusChip, DataAge, DrugName, ErrorBox, Icon, Loading, Stepper, hiName, useNow, when } from "@/components/ui";

type Result = "confirmed_stockout" | "stock_available" | "household_only";
const CHOICES: { k: Result; hi: string; en: string; icon: string; ground: string }[] = [
  { k: "confirmed_stockout", hi: "स्टॉक ख़त्म", en: "Out of stock", icon: "out-of-stock", ground: "var(--status-out-bg)" },
  { k: "stock_available", hi: "स्टॉक है", en: "Stock is available", icon: "check-circle", ground: "var(--status-ok-bg)" },
  { k: "household_only", hi: "मरीज़ के पास घर पर है", en: "Patient still has some at home", icon: "home", ground: "var(--status-wait-bg)" },
];

export default function VerifyPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const ref = useRefData();
  const now = useNow();
  const detail = useLoad(async () => {
    const c = await api.caseDetail(id);
    const [patient, stock] = await Promise.all([
      api.patient(c.patient_id).catch(() => null),
      api.stock(c.facility_id).catch(() => null),
    ]);
    return { c, patient, snap: stock?.find((s) => s.drug_id === c.drug_id) ?? null };
  }, `verify-${id}`);
  const [result, setResult] = useState<Result | null>(null);
  const [count, setCount] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);

  const d = detail.data;
  const onHand = count ?? d?.snap?.on_hand ?? 0;

  const submit = async () => {
    if (!result) return;
    setBusy(true);
    setErr(null);
    try {
      await api.verify(id, result, result === "household_only" ? null : onHand);
      router.push("/pharmacist");
    } catch (e) {
      setErr(e);
      setBusy(false);
    }
  };

  if (!d) {
    return (
      <PhoneShell title={{ hi: "जाँचें", en: "Verify" }} back="/pharmacist">
        {detail.loading ? <Loading /> : <ErrorBox error={detail.error} onRetry={detail.reload} />}
      </PhoneShell>
    );
  }
  const { c, patient } = d;
  const w = when(c.created_at);
  const done = c.status !== "reported";

  return (
    <PhoneShell title={{ hi: "रिपोर्ट जाँचें", en: "Verify report" }} back="/pharmacist" tabs={false}
      foot={!done ? (
        <button type="button" className="sa-btn sa-btn--hero" data-testid="verify-submit" disabled={!result || busy} onClick={submit}>
          <Icon name="check" size={28} /><Bi hi="पुष्टि करें" en="Confirm finding" />
        </button>
      ) : undefined}>
      <section className="sa-card" style={{ gap: 12 }}>
        <div className="sa-card-head">
          <span style={{ font: "600 17px/24px var(--font-sans)" }}>
            {patient ? <Bi hi={`${hiName(patient)}, ${patient.age}`} en={`${patient.name}, ${patient.age}`} /> : c.patient_id}
          </span>
          <CaseStatusChip status={c.status} />
        </div>
        <span className="m-caption" style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <Icon name={c.channel === "voice" ? "mic" : "edit"} size={16} />
          <Bi inline hi={`${c.channel === "voice" ? "बोलकर" : "लिखकर"} · ${w.hi}`} en={`${c.channel === "voice" ? "by voice" : "typed"} · ${w.en}`} />
        </span>
        <div className="kv"><Bi hi="दवा" en="Medicine" /><b><DrugName d={ref.drug(c.drug_id)} id={c.drug_id} /></b></div>
        <div className="kv"><Bi hi="माँगी" en="Asked for" /><b className="num">{c.requested_qty}</b></div>
        <div className="kv"><Bi hi="घर पर बची (दिन)" en="Left at home (days)" /><b className="num">{c.household_supply_days}</b></div>
      </section>

      {c.transcript && (
        <section className="sa-card" style={{ gap: 8 }}>
          <span className="m-caption" style={{ fontWeight: 600 }}><Bi inline hi="उन्होंने क्या कहा" en="What they said" /></span>
          <blockquote style={{ margin: 0, padding: "4px 0 4px 12px", boxShadow: "inset 3px 0 0 var(--line-strong)", font: "400 16px/27px var(--font-hindi)" }}>“{c.transcript}”</blockquote>
        </section>
      )}

      {done ? (
        <div className="sa-banner sa-banner--ok"><span className="sa-banner-ic"><Icon name="check-circle" /></span><Bi hi="यह रिपोर्ट जाँची जा चुकी है" en="This report has already been verified" /></div>
      ) : (
        <>
          <section className="sa-card" style={{ gap: 10 }}>
            <div className="sa-card-head">
              <span className="m-caption" style={{ fontWeight: 600 }}><Bi inline hi="अलमारी में अभी कितनी?" en="Count the shelf now" /></span>
              {d.snap && <DataAge iso={d.snap.recorded_at} now={now} />}
            </div>
            {d.snap && <span className="m-caption"><Bi inline hi={`पिछली गिनती: ${d.snap.on_hand} गोलियाँ`} en={`Last count: ${d.snap.on_hand} tablets`} /></span>}
            <Stepper value={onHand} onChange={setCount} step={10} label={{ hi: "गोलियाँ", en: "Tablets on hand" }} testId="on-hand" />
          </section>

          <h2 className="m-heading" style={{ fontSize: 18 }}><Bi inline hi="आपने क्या पाया?" en="What did you find?" /></h2>
          <div role="radiogroup" aria-label="Finding · नतीजा" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {CHOICES.map((ch) => (
              <button key={ch.k} type="button" role="radio" aria-checked={result === ch.k} data-testid={`result-${ch.k}`}
                className={`pick${result === ch.k ? " is-on" : ""}`} onClick={() => setResult(ch.k)}>
                <span className="pick-art" style={{ width: 48, height: 48, background: ch.ground }}><Icon name={ch.icon} /></span>
                <span style={{ flex: 1, font: "600 17px/24px var(--font-sans)" }}><Bi hi={ch.hi} en={ch.en} /></span>
                <span className="pick-radio">{result === ch.k && <Icon name="check" size={16} />}</span>
              </button>
            ))}
          </div>
          {result === "confirmed_stockout" && (
            <p className="m-caption"><Bi hi="ज़िला अधिकारी को तुरंत चेतावनी जाएगी" en="The district officer is alerted right away" /></p>
          )}
        </>
      )}
      {err ? <ErrorBox error={err} /> : null}
    </PhoneShell>
  );
}
