"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, Case, Transfer, isNoTransfer } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useRefData } from "@/lib/hooks";
import { Bi, ErrorBox, Icon, Tone } from "./ui";

/** The officer's district, or "" until reference data has loaded (so pages fetch the overview once, not twice). */
export function useDistrict(): string {
  const { user } = useAuth();
  const ref = useRefData();
  if (!ref.data) return "";
  return ref.facility(user?.facility_id ?? "")?.district ?? ref.data.facilities[0]?.district ?? "";
}

/** A promise that never settles — used to hold a load until its inputs are ready. */
export const pending = <T,>() => new Promise<T>(() => {});

export const WARN: Record<string, { tone: Tone; hi: string; en: string }> = {
  critical: { tone: "out", hi: "गंभीर", en: "Critical" },
  low: { tone: "low", hi: "कम", en: "Low" },
  ok: { tone: "ok", hi: "ठीक", en: "OK" },
};

const REASON: Record<string, { hi: string; en: string }> = {
  needs_split_or_supply: { hi: "कोई एक केंद्र अपना सुरक्षित स्टॉक रखकर पूरी मात्रा नहीं भेज सकता — ज़िला भंडार से मँगवाएँ।", en: "No single centre can send the full amount and keep its own safety stock — escalate to the district store." },
};

/** "Draft a transfer" — asks the engine (+ AI rationale); opens the draft or shows why none is possible. */
export function DraftButton({ c, onDone }: { c: Case; onDone?: () => void }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [none, setNone] = useState<string | null>(null);
  const [err, setErr] = useState<unknown>(null);
  const go = async () => {
    setBusy(true);
    setErr(null);
    try {
      const r = await api.draftTransfer(c.id);
      if (isNoTransfer(r)) {
        setNone(r.reason);
        onDone?.();
      } else router.push(`/district/transfers/${r.id}`);
    } catch (e) {
      setErr(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {c.transfer_id && c.status === "transfer_drafted" ? (
        <button type="button" className="sa-btn sa-btn--web" onClick={() => router.push(`/district/transfers/${c.transfer_id}`)}>
          <Icon name="transfer" size={20} /><Bi hi="मसौदा देखें" en="Review draft" />
        </button>
      ) : (
        <button type="button" className="sa-btn sa-btn--web" data-testid={`draft-${c.id}`} disabled={busy} onClick={go}>
          <Icon name="suggest" size={20} /><Bi hi={busy ? "AI मसौदा बना रहा है…" : "ट्रांसफ़र का मसौदा बनाएँ"} en={busy ? "AI is drafting…" : "Draft a transfer"} />
        </button>
      )}
      {none && (
        <div className="sa-banner sa-banner--low" data-testid="no-transfer">
          <span className="sa-banner-ic"><Icon name="alert" /></span>
          <span><Bi hi="सुरक्षित ट्रांसफ़र संभव नहीं" en="No safe transfer possible" /><span className="d-caption" style={{ display: "block" }}><Bi hi={REASON[none]?.hi ?? none} en={REASON[none]?.en ?? none} /></span></span>
        </div>
      )}
      {err ? <ErrorBox error={err} /> : null}
    </div>
  );
}

export const TRANSFER_STATUS: Record<Transfer["status"], { tone: Tone; hi: string; en: string; icon: string }> = {
  draft: { tone: "wait", hi: "मंज़ूरी बाकी", en: "Waiting for approval", icon: "suggest" },
  approved: { tone: "wait", hi: "मंज़ूर — भेजना बाकी", en: "Approved — not dispatched", icon: "check" },
  rejected: { tone: "out", hi: "रद्द", en: "Rejected", icon: "close" },
  dispatched: { tone: "wait", hi: "रास्ते में", en: "Dispatched", icon: "truck" },
  received: { tone: "ok", hi: "पहुँच गया", en: "Received", icon: "check-circle" },
  cancelled: { tone: "wait", hi: "रद्द", en: "Cancelled", icon: "close" },
};
