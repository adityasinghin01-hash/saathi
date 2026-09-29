"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, Patient, VoiceResult } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useOfflineQueue } from "@/lib/OfflineQueueContext";
import { useLanguage } from "@/i18n/LanguageProvider";
import { useLoad, useRefData } from "@/lib/hooks";
import { PhoneShell } from "@/components/shells";
import { AiBadge, Bi, DrugName, Empty, ErrorBox, Icon, Loading, Status, hiName, initials } from "@/components/ui";

type Step = "pick" | "speak" | "check" | "sending";

interface Form {
  drug_id: string;
  requested_qty: number | null;
  household_supply_days: number | null;
  date: string; // yyyy-mm-dd
}

const today = () => new Date().toISOString().slice(0, 10);

function ReportFlow() {
  const { user } = useAuth();
  const { lang, both } = useLanguage();
  const { isOffline, enqueue } = useOfflineQueue();
  const router = useRouter();
  const params = useSearchParams();
  const ref = useRefData();
  const isAsha = user?.role === "asha";

  const [patientId, setPatientId] = useState<string>(params.get("patient") ?? (isAsha ? "" : user?.patient_id ?? ""));
  const [step, setStep] = useState<Step>(isAsha && !params.get("patient") ? "pick" : "speak");
  const [typing, setTyping] = useState(false);
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [heard, setHeard] = useState<VoiceResult | null>(null);
  const [note, setNote] = useState("");
  const [form, setForm] = useState<Form>({ drug_id: "", requested_qty: null, household_supply_days: null, date: today() });
  const [err, setErr] = useState<unknown>(null);
  const [offlineSaved, setOfflineSaved] = useState(false);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  const patients = useLoad(() => (isAsha ? api.patients() : Promise.resolve([] as Patient[])), `pts-${isAsha}`);
  const patient = useLoad(() => (patientId ? api.patient(patientId) : Promise.resolve(null)), `pt-${patientId}`);
  const rxDrugs = useMemo(() => patient.data?.prescriptions.filter((p) => p.active).map((p) => p.drug_id) ?? [], [patient.data]);
  // Only offer medicines once the patient's prescriptions are known (the backend rejects others).
  const drugChoices = useMemo(() => (patient.loading ? [] : rxDrugs.length ? rxDrugs : ref.data?.drugs.map((d) => d.id) ?? []), [patient.loading, rxDrugs, ref.data]);

  useEffect(() => {
    // Pick a default medicine for the typed path, but never fill one in when the voice report didn't name it.
    const voiceMissedDrug = heard && !heard.fields.drug_id && form.drug_id === "";
    if (drugChoices.length && !voiceMissedDrug && !drugChoices.includes(form.drug_id)) setForm((f) => ({ ...f, drug_id: drugChoices[0] })); // eslint-disable-line react-hooks/set-state-in-effect -- keep the chosen medicine valid for this patient
  }, [drugChoices, form.drug_id, heard]);

  useEffect(() => {
    if (!recording) return;
    const t = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [recording]);

  const startRec = async () => {
    setErr(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunks.current = [];
      mr.ondataavailable = (e) => e.data.size && chunks.current.push(e.data);
      mr.onstop = () => stream.getTracks().forEach((t) => t.stop());
      mr.start();
      recorder.current = mr;
      setSeconds(0);
      setRecording(true);
    } catch (e) {
      setErr(e);
      setTyping(true);
    }
  };

  const stopAndSend = async () => {
    const mr = recorder.current;
    if (!mr) return;
    const done = new Promise<void>((r) => mr.addEventListener("stop", () => r(), { once: true }));
    mr.stop();
    setRecording(false);
    await done;
    setStep("sending");
    try {
      // Browsers label recordings "audio/webm;codecs=opus"; send the bare type the backend accepts.
      const audio = new Blob(chunks.current, { type: (mr.mimeType || "audio/webm").split(";")[0] });
      const res = await api.voice(audio, lang, patientId);
      setHeard(res);
      setForm({
        drug_id: res.fields.drug_id ?? "",
        requested_qty: res.fields.requested_qty,
        household_supply_days: res.fields.household_supply_days,
        date: (res.fields.attempted_at ?? "").slice(0, 10),
      });
      setStep("check");
    } catch (e) {
      setErr(e);
      setStep("speak");
    }
  };

  const submit = async () => {
    setErr(null);
    const fields = {
      patient_id: patientId,
      drug_id: form.drug_id,
      requested_qty: form.requested_qty ?? 0,
      household_supply_days: form.household_supply_days ?? 0,
      attempted_at: `${form.date}T09:00:00Z`,
    };
    setStep("sending");
    try {
      if (isOffline || (typeof navigator !== "undefined" && !navigator.onLine)) {
        await enqueue({ method: "POST", path: "/cases", body: { ...fields, channel: heard ? "voice" : "manual", transcript: heard?.transcript ?? (note || undefined) } });
        setOfflineSaved(true);
        setStep("check");
        return;
      }
      const created = heard
        ? await api.confirmVoice(fields, heard.transcript)
        : await api.createCase({ ...fields, channel: "manual", transcript: note || undefined });
      router.push(`/patient/cases/${created.id}`);
    } catch (e) {
      setErr(e);
      setStep("check");
    }
  };

  const set = (k: keyof Form, v: string) => setForm((f) => ({ ...f, [k]: k === "drug_id" || k === "date" ? v : v === "" ? null : Math.max(0, Number(v) || 0) }));
  const missing = {
    drug_id: !form.drug_id,
    requested_qty: !form.requested_qty,
    household_supply_days: form.household_supply_days === null,
    date: !form.date,
  };
  const complete = !Object.values(missing).some(Boolean);
  const missingNote = (k: keyof typeof missing) =>
    missing[k] ? <span className="sa-help is-error" data-testid={`missing-${k}`}><Bi inline hi={heard ? "सुनाई नहीं दिया — भरें" : "भरें"} en={heard ? "Not heard — please fill in" : "Please fill in"} /></span> : null;
  const pName = patient.data ? (lang === "hi" ? hiName(patient.data) : patient.data.name) : "";

  /* ---------- step: ASHA picks a patient ---------- */
  if (step === "pick") {
    return (
      <PhoneShell title={{ hi: "किसके लिए?", en: "Reporting for" }} back="/asha">
        <h1 className="m-title hd"><Bi hi="किस मरीज़ के लिए?" en="Which patient?" /></h1>
        {patients.loading && <Loading />}
        {patients.error ? <ErrorBox error={patients.error} onRetry={patients.reload} /> : null}
        {patients.data?.length === 0 && <Empty hi="कोई मरीज़ नहीं" en="No patients assigned" />}
        <div className="sa-rows">
          {patients.data?.map((p) => (
            <button key={p.id} type="button" className="sa-row" data-testid={`pick-${p.id}`} style={{ minHeight: 72, width: "100%", textAlign: "left", border: 0, background: "none" }}
              onClick={() => { setPatientId(p.id); setStep("speak"); }}>
              <span className="sa-avatar sa-avatar--sunk">{initials(p.name)}</span>
              <span className="sa-row-main" style={{ font: "600 16px/22px var(--font-sans)" }}><Bi hi={`${hiName(p)}, ${p.age}`} en={`${p.name}, ${p.age}`} /></span>
              <Icon name="chevron-right" />
            </button>
          ))}
        </div>
      </PhoneShell>
    );
  }

  /* ---------- step: check the details ---------- */
  if (step === "check" || (step === "sending" && (heard || typing))) {
    return (
      <PhoneShell title={{ hi: "जाँच लें", en: "Check the details" }} back={undefined} tabs={false}
        foot={
          offlineSaved ? (
            <button type="button" className="sa-btn sa-btn--hero" onClick={() => router.push(isAsha ? "/asha" : "/patient")}><Icon name="home" size={28} /><Bi hi="घर पर जाएँ" en="Go home" /></button>
          ) : (
            <>
              <button type="button" className="sa-btn sa-btn--hero" data-testid="confirm-send" disabled={step === "sending" || !complete || !patientId} onClick={submit}>
                <Icon name="check" size={28} /><Bi hi="सही है, भेजें" en="Confirm & send" />
              </button>
              <button type="button" className="sa-btn sa-btn--ghost sa-btn--block" onClick={() => { setHeard(null); setTyping(false); setStep("speak"); }}>
                <Icon name="mic" /><Bi hi="फिर से बोलें" en="Record again" />
              </button>
            </>
          )
        }>
        {isAsha && pName && <Status tone="wait" icon="user-group" hi={`${pName} के लिए`} en={`Reporting for ${pName}`} />}
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <h1 className="m-title hd"><Bi hi={heard ? "हमने यह समझा" : "क्या हुआ, भरें"} en={heard ? "Here's what we understood" : "Fill in what happened"} /></h1>
          <p className="m-caption"><Bi hi="कुछ ग़लत हो तो बदल दें" en="Change anything that's wrong" /></p>
        </div>
        {heard && (
          <section className="sa-card" style={{ gap: 8 }}>
            <span className="m-caption" style={{ fontWeight: 600 }}><Bi inline hi="हमने यह सुना" en="What we heard" /></span>
            <p data-testid="transcript" style={{ margin: 0, font: "400 17px/28px var(--font-hindi)" }}>{heard.transcript}</p>
            <AiBadge source={heard.ai_source} model={heard.ai_model} />
          </section>
        )}
        {heard?.not_a_refill_report && (
          <div className="sa-banner sa-banner--low" data-testid="not-a-refill"><span className="sa-banner-ic"><Icon name="alert" /></span>
            <Bi hi="इसमें दवा न मिलने की बात सुनाई नहीं दी। नीचे भरें या फिर से बोलें।" en="We didn't hear a missed refill in this. Fill it in below or record again." /></div>
        )}
        {err ? <ErrorBox error={err} /> : null}
        {offlineSaved && (
          <div className="sa-banner sa-banner--offline" data-testid="saved-offline" role="status"><span className="sa-banner-ic"><Icon name="cloud-off" /></span>
            <Bi hi="ऑफ़लाइन सहेजा गया — इंटरनेट आने पर भेजेंगे" en="Saved offline — will send when online" /></div>
        )}
        <div className="sa-rows" style={{ padding: "4px 0" }}>
          <label className="sa-field" style={{ padding: "8px 16px" }}>
            <span className="sa-field-label"><Bi hi="दवा" en="Medicine" /></span>
            <span className="sa-input"><select data-testid="f-drug" value={form.drug_id} onChange={(e) => set("drug_id", e.target.value)} style={{ border: 0, background: "transparent", width: "100%", fontSize: 17 }}>
              {!form.drug_id && <option value="">{both("— दवा चुनें —", "— choose medicine —")}</option>}
              {drugChoices.map((id) => { const d = ref.drug(id); return <option key={id} value={id}>{d ? `${hiName(d, "drug")} · ${d.name} ${d.strength}` : id}</option>; })}
            </select></span>
            {missingNote("drug_id")}
          </label>
          <label className="sa-field" style={{ padding: "8px 16px" }}>
            <span className="sa-field-label"><Bi hi="कब गए" en="Date you went" /></span>
            <span className="sa-input"><input type="date" data-testid="f-date" value={form.date} max={today()} onChange={(e) => set("date", e.target.value)} /></span>
            {missingNote("date")}
          </label>
          <div className="grid-2" style={{ padding: "8px 16px", gap: 12 }}>
            <label className="sa-field">
              <span className="sa-field-label"><Bi hi="कितनी माँगी" en="Asked for" /></span>
              <span className="sa-input"><input type="number" inputMode="numeric" min={1} data-testid="f-qty" value={form.requested_qty ?? ""} onChange={(e) => set("requested_qty", e.target.value)} /></span>
              {missingNote("requested_qty")}
            </label>
            <label className="sa-field">
              <span className="sa-field-label"><Bi hi="घर पर बची (दिन)" en="Left at home (days)" /></span>
              <span className="sa-input"><input type="number" inputMode="numeric" min={0} data-testid="f-home" value={form.household_supply_days ?? ""} onChange={(e) => set("household_supply_days", e.target.value)} /></span>
              {missingNote("household_supply_days")}
            </label>
          </div>
          {!heard && (
            <label className="sa-field" style={{ padding: "8px 16px" }}>
              <span className="sa-field-label"><Bi hi="और कुछ? (ज़रूरी नहीं)" en="Anything else? (optional)" /></span>
              <span className="sa-input" style={{ alignItems: "flex-start" }}><textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder={both("जैसे: PHC पर मेटफॉर्मिन नहीं मिली", "e.g. Didn't get Metformin at the PHC")} /></span>
            </label>
          )}
        </div>
        <div className="sa-banner" style={{ background: "var(--status-wait-bg)", color: "var(--status-wait)" }}>
          <span className="sa-banner-ic"><Icon name="clock" /></span>
          <Bi hi="यह रिपोर्ट है, अभी पुष्टि नहीं — फ़ार्मासिस्ट स्टॉक देखकर पक्का करेंगे" en="Reported — not yet confirmed. The pharmacist will check the shelf." />
        </div>
      </PhoneShell>
    );
  }

  /* ---------- step: speak (or type) ---------- */
  return (
    <PhoneShell title={{ hi: "बोलकर बताएँ", en: "Tell us by voice" }} back={isAsha ? "/asha" : "/patient"} tabs={false}
      foot={
        <>
          {recording ? (
            <button type="button" className="sa-btn sa-btn--hero" data-testid="stop-send" onClick={stopAndSend}><Icon name="check" size={28} /><Bi hi="रोकें और जाँचें" en="Stop & check" /></button>
          ) : null}
          <div className="grid-2" style={{ gap: 8 }}>
            <button type="button" className="sa-btn sa-btn--outline" data-testid="type-instead" onClick={() => { setTyping(true); setHeard(null); setStep("check"); }} style={{ padding: "8px 12px", fontSize: 16 }}>
              <Icon name="edit" /><Bi hi="लिखकर बताएँ" en="Type instead" />
            </button>
            <button type="button" className="sa-btn sa-btn--ghost" onClick={() => router.push(isAsha ? "/asha" : "/patient")} style={{ padding: "8px 12px", fontSize: 16 }}>
              <Icon name="close" /><Bi hi="रद्द करें" en="Cancel" />
            </button>
          </div>
        </>
      }>
      {isAsha && pName && <Status tone="wait" icon="user-group" hi={`${pName} के लिए`} en={`Reporting for ${pName}`} />}
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <h1 className="m-title hd"><Bi hi="क्या हुआ? बस बोलिए" en="What happened? Just speak" /></h1>
        <p className="m-caption"><Bi hi="कौन-सी दवा, किस केंद्र पर, कब गए, घर पर कितनी बची" en="Which medicine, which centre, when you went, how much is left" /></p>
      </div>
      {err ? <ErrorBox error={err} /> : null}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: "24px 0 8px" }}>
        {step === "sending" ? (
          <>
            <Loading />
            <span className="m-body"><Bi hi="सुन रहे हैं, समझ रहे हैं…" en="Listening and understanding…" /></span>
          </>
        ) : (
          <>
            <button type="button" className={`sa-mic${recording ? " is-listening" : ""}`} aria-pressed={recording} data-testid="mic"
              aria-label={recording ? both("रोकें", "Stop") : both("बोलना शुरू करें", "Start speaking")}
              disabled={isOffline}
              onClick={recording ? stopAndSend : startRec} style={{ width: 120, height: 120 }}>
              <Icon name="mic" size={48} />
            </button>
            <span style={{ display: "flex", gap: 8, alignItems: "center", font: "600 15px/22px var(--font-sans)" }}>
              {recording && <span className="rec-dot" />}
              {recording && <span className="num">{Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}</span>}
              <Bi inline hi={recording ? "सुन रहे हैं…" : isOffline ? "आवाज़ के लिए इंटरनेट चाहिए — लिखकर बताएँ" : "माइक दबाकर बोलिए"} en={recording ? "Listening…" : isOffline ? "Voice needs internet — please type instead" : "Tap the mic and speak"} />
            </span>
          </>
        )}
      </div>
      {patient.data && rxDrugs.length > 0 && (
        <p className="m-caption" style={{ textAlign: "center" }}>
          <Bi inline hi="आपकी दवाइयाँ:" en="Your medicines:" />{" "}
          {rxDrugs.map((id, i) => <span key={id}>{i ? ", " : ""}<DrugName d={ref.drug(id)} id={id} /></span>)}
        </p>
      )}
    </PhoneShell>
  );
}

export default function ReportPage() {
  return (
    <Suspense fallback={<div className="center-page"><Loading /></div>}>
      <ReportFlow />
    </Suspense>
  );
}
