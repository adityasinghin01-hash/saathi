"use client";

import React from "react";
import { ICONS } from "./icons-data";
import { useLanguage } from "@/i18n/LanguageProvider";
import type { AiSource, CaseStatus, Drug, Facility, Named } from "@/lib/api";

/** Both languages, always (Saathi rule). CSS orders them by html[data-lang]. */
export function Bi({ hi, en, inline, className, style }: { hi: React.ReactNode; en: React.ReactNode; inline?: boolean; className?: string; style?: React.CSSProperties }) {
  return (
    <span className={`sa-bi${inline ? " sa-bi--inline" : ""}${className ? ` ${className}` : ""}`} style={style}>
      <span lang="hi">{hi}</span>
      <span lang="en">{en}</span>
    </span>
  );
}

export function Icon({ name, size, style, className }: { name: string; size?: 16 | 20 | 24 | 28 | 32 | 40 | 48; style?: React.CSSProperties; className?: string }) {
  const cls = `ic${size && size !== 24 ? ` ic-${size}` : ""}${className ? ` ${className}` : ""}`;
  const dims = size === 48 ? { width: 48, height: 48 } : undefined;
  return <svg className={cls} viewBox="0 0 24 24" aria-hidden="true" style={{ ...dims, ...style }} dangerouslySetInnerHTML={{ __html: ICONS[name] ?? "" }} />;
}

export function LangToggle({ small = true }: { small?: boolean }) {
  const { lang, setLang, both } = useLanguage();
  return (
    <div className={`sa-lang${small ? " sa-lang--sm" : ""}`} role="group" aria-label={both("भाषा", "Language")}>
      <button type="button" aria-pressed={lang === "hi"} onClick={() => setLang("hi")}>हिं</button>
      <button type="button" aria-pressed={lang === "en"} onClick={() => setLang("en")}>EN</button>
    </div>
  );
}

export function DemoBadge({ long }: { long?: boolean }) {
  return long ? (
    <span className="sa-demo"><Bi inline hi="नमूना डेटा" en="SYNTHETIC DEMO DATA" /></span>
  ) : (
    <span className="sa-demo">DEMO</span>
  );
}

export function Loading() {
  const { both } = useLanguage();
  return (
    <div className="sa-state" role="status" aria-label={both("लोड हो रहा है", "Loading")}>
      <span className="sa-skel" style={{ width: "100%", height: 64, borderRadius: 16, display: "block" }} />
      <span className="sa-skel" style={{ width: "70%", height: 20, borderRadius: 8, display: "block", marginTop: 12 }} />
    </div>
  );
}

export function ErrorBox({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <div className="sa-banner sa-banner--out" role="alert">
      <span className="sa-banner-ic"><Icon name="alert" /></span>
      <span style={{ flex: 1 }}>
        <Bi hi="कुछ गड़बड़ हुई" en="Something went wrong" />
        <span className="m-caption" style={{ display: "block" }}>{msg}</span>
      </span>
      {onRetry && (
        <button type="button" className="sa-btn sa-btn--secondary sa-btn--web" onClick={onRetry}>
          <Icon name="refresh" size={20} /><Bi hi="फिर से" en="Retry" />
        </button>
      )}
    </div>
  );
}

export function Empty({ hi, en, art = "medkit" }: { hi: string; en: string; art?: string }) {
  return (
    <div className="sa-state bi-c" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, padding: "24px 8px", textAlign: "center" }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={`/art/${art}.webp`} alt="" width={96} height={96} style={{ objectFit: "contain" }} />
      <Bi hi={hi} en={en} />
    </div>
  );
}

export type Tone = "out" | "low" | "ok" | "wait";
const TONE_ICON: Record<Tone, string> = { out: "out-of-stock", low: "alert", ok: "check-circle", wait: "clock" };

export function Status({ tone, hi, en, icon, large }: { tone: Tone; hi: string; en: string; icon?: string; large?: boolean }) {
  return (
    <span className={`sa-status sa-status--${tone}${large ? " sa-status--lg" : ""}`}>
      <Icon name={icon ?? TONE_ICON[tone]} size={16} />
      <Bi inline hi={hi} en={en} />
    </span>
  );
}

export const CASE_STATUS: Record<CaseStatus, { hi: string; en: string; tone: Tone; icon: string }> = {
  reported: { hi: "शिकायत दर्ज", en: "Reported", tone: "wait", icon: "clock" },
  verified: { hi: "फ़ार्मासिस्ट ने जाँचा", en: "Verified", tone: "out", icon: "out-of-stock" },
  transfer_drafted: { hi: "ट्रांसफ़र का मसौदा", en: "Transfer drafted", tone: "wait", icon: "transfer" },
  transfer_approved: { hi: "ट्रांसफ़र मंज़ूर", en: "Transfer approved", tone: "wait", icon: "check" },
  dispatched: { hi: "दवा रास्ते में", en: "Dispatched", tone: "wait", icon: "truck" },
  received: { hi: "केंद्र पहुँची", en: "Received at centre", tone: "ok", icon: "health-centre" },
  partially_supplied: { hi: "कुछ दवा मिली", en: "Partly given", tone: "low", icon: "hand-over" },
  supplied: { hi: "दवा दे दी गई", en: "Supplied", tone: "ok", icon: "hand-over" },
  closed: { hi: "मामला बंद", en: "Closed", tone: "ok", icon: "check-circle" },
  cancelled: { hi: "रद्द", en: "Cancelled", tone: "wait", icon: "close" },
};

export function CaseStatusChip({ status, large }: { status: CaseStatus; large?: boolean }) {
  const s = CASE_STATUS[status] ?? { hi: status, en: status, tone: "wait" as Tone, icon: "clock" };
  return <span data-testid="case-status" data-status={status}><Status tone={s.tone} hi={s.hi} en={s.en} icon={s.icon} large={large} /></span>;
}

export function AiBadge({ source, model }: { source?: AiSource; model?: string }) {
  if (source === "gemini") {
    return (
      <span className="sa-ai"><span className="sa-ai-ic"><Icon name="suggest" size={16} /></span>
        <Bi inline hi="AI का मसौदा — आपकी मंज़ूरी ज़रूरी" en={`Drafted by AI${model ? ` (${model})` : ""} — needs your approval`} />
      </span>
    );
  }
  return (
    <span className="sa-ai" style={{ background: "var(--status-wait-bg)", color: "var(--status-wait)" }} data-testid="ai-fallback">
      <span className="sa-ai-ic"><Icon name="cloud-off" size={16} /></span>
      <Bi inline hi="नियमों से बना — AI उपलब्ध नहीं था" en="Drafted by rules — AI unavailable" />
    </span>
  );
}

/* ---------- names (English + Hindi) ---------- */
const FACILITY_HI: Record<string, string> = {
  "phc-1": "सुंदरपुर PHC", "phc-2": "नयागाँव PHC", "phc-3": "अमरपुर PHC", "phc-4": "शांतिपुर PHC",
  "phc-5": "नवग्राम PHC", "phc-6": "उदयपुर PHC", "store-1": "सूर्यनगर ज़िला भंडार",
};
const DRUG_HI: Record<string, string> = { metformin: "मेटफॉर्मिन", glimepiride: "ग्लिमेपिराइड", amlodipine: "एम्लोडिपिन", telmisartan: "टेल्मिसार्टन" };

export function hiName(x: (Named & { id: string }) | undefined, kind: "facility" | "drug" | "person" = "person"): string {
  if (!x) return "—";
  if (x.name_hi) return x.name_hi;
  if (kind === "facility") return FACILITY_HI[x.id] ?? x.name;
  if (kind === "drug") return DRUG_HI[x.id] ?? x.name;
  return x.name;
}

export function FacilityName({ f, id, inline = true }: { f?: Facility; id?: string; inline?: boolean }) {
  if (!f) return <>{id ?? "—"}</>;
  return <Bi inline={inline} hi={hiName(f, "facility")} en={f.name} />;
}

export function DrugName({ d, id, inline = true }: { d?: Drug; id?: string; inline?: boolean }) {
  if (!d) return <>{id ?? "—"}</>;
  return <Bi inline={inline} hi={`${hiName(d, "drug")} ${d.strength}`} en={`${d.name} ${d.strength}`} />;
}

export function initials(name: string): string {
  const clean = name.replace(/^(Synthetic|Dr\.?)\s+/i, "");
  return clean.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]?.toUpperCase()).join("") || "?";
}

/* ---------- time ---------- */
const HI_MONTHS = ["जन.", "फ़र.", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अग.", "सितंबर", "अक्टू.", "नवं.", "दिसं."];
export function when(iso: string): { hi: string; en: string } {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return { hi: iso, en: iso };
  const time = d.toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" });
  return { hi: `${d.getDate()} ${HI_MONTHS[d.getMonth()]}, ${time}`, en: `${d.getDate()} ${d.toLocaleString("en-IN", { month: "short" })}, ${time}` };
}

export function age(iso: string, now: number): { hi: string; en: string; tone: Tone } {
  const mins = Math.max(0, Math.round((now - new Date(iso).getTime()) / 60000));
  if (mins < 60) return { hi: `${mins} मिनट पहले`, en: `${mins} min ago`, tone: "ok" };
  const h = Math.round(mins / 60);
  if (h < 48) return { hi: `${h} घंटे पहले`, en: `${h} h ago`, tone: h > 24 ? "low" : "ok" };
  const days = Math.round(h / 24);
  return { hi: `${days} दिन पहले`, en: `${days} days ago`, tone: "out" };
}

export function DataAge({ iso, now }: { iso: string; now: number }) {
  const a = age(iso, now);
  return (
    <span className="sa-age" title={iso}>
      <span className="sa-age-dot" style={{ background: `var(--status-${a.tone}-solid)` }} />
      <Bi inline hi={`अपडेट ${a.hi}`} en={`updated ${a.en}`} />
    </span>
  );
}

/** Stable "now" for a render pass (keeps render pure for the React compiler lint). */
export function useNow(refreshMs = 60000): number {
  const [now, setNow] = React.useState(() => Date.now());
  React.useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), refreshMs);
    return () => clearInterval(t);
  }, [refreshMs]);
  return now;
}

/** − value + stepper (design: .stepper). */
export function Stepper({ value, onChange, step = 1, min = 0, label, testId }: { value: number; onChange: (v: number) => void; step?: number; min?: number; label: { hi: string; en: string }; testId?: string }) {
  const { both } = useLanguage();
  return (
    <div className="stepper" role="group" aria-label={both(label.hi, label.en)}>
      <button type="button" onClick={() => onChange(Math.max(min, value - step))} aria-label={both(`${step} कम`, `${step} fewer`)}><Icon name="minus" /></button>
      <input type="number" inputMode="numeric" data-testid={testId} value={value} min={min}
        onChange={(e) => onChange(Math.max(min, Number(e.target.value) || 0))}
        aria-label={both(label.hi, label.en)}
        style={{ width: 96, textAlign: "center", border: 0, background: "transparent", font: "600 24px/32px var(--font-sans)", fontVariantNumeric: "tabular-nums" }} />
      <button type="button" onClick={() => onChange(value + step)} aria-label={both(`${step} ज़्यादा`, `${step} more`)}><Icon name="plus" /></button>
    </div>
  );
}
