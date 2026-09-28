"use client";

import { useState } from "react";
import { api, Role, User } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useLoad } from "@/lib/hooks";
import { Bi, DemoBadge, ErrorBox, Icon, LangToggle, Loading } from "@/components/ui";

const ROLE_CARD: Record<Role, { hi: string; en: string; art: string; ground: string; noteHi: string; noteEn: string }> = {
  patient: { hi: "मरीज़", en: "Patient", art: "home", ground: "g-leaf", noteHi: "दवा नहीं मिली? बोलकर बताइए", noteEn: "Didn't get medicine? Say it" },
  asha: { hi: "आशा दीदी", en: "ASHA worker", art: "home", ground: "g-mari", noteHi: "अपने मरीज़ों के लिए रिपोर्ट करें", noteEn: "Report for your patients" },
  pharmacist: { hi: "फ़ार्मासिस्ट", en: "Pharmacist", art: "shelf", ground: "g-clay", noteHi: "स्टॉक जाँचें, दवा दें", noteEn: "Check the shelf, hand over" },
  district_officer: { hi: "ज़िला अधिकारी", en: "District officer", art: "van", ground: "g-sunk", noteHi: "कमी देखें, ट्रांसफ़र मंज़ूर करें", noteEn: "See shortages, approve transfers" },
};

export default function LoginPage() {
  const { login } = useAuth();
  const users = useLoad(async () => {
    const [all, ids] = await Promise.all([api.demoUsers(), api.scenario()]);
    const cast: User[] = [];
    const patientUser = all.find((u) => u.role === "patient" && u.patient_id === ids.patient_id);
    for (const id of [patientUser?.id, ids.asha_id, ids.pharmacist_id, ids.district_officer_id]) {
      const u = all.find((x) => x.id === id);
      if (u) cast.push(u);
    }
    return { cast, all };
  }, "users");
  const [busy, setBusy] = useState<string | null>(null);
  const [resetAt, setResetAt] = useState<string | null>(null);
  const [err, setErr] = useState<unknown>(null);

  const go = async (id: string) => {
    setBusy(id);
    setErr(null);
    try {
      await login(id);
    } catch (e) {
      setErr(e);
      setBusy(null);
    }
  };

  const reset = async () => {
    setBusy("reset");
    setErr(null);
    try {
      const r = await api.resetDemo();
      setResetAt(r.seeded_at);
      users.reload();
    } catch (e) {
      setErr(e);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="phone-frame" style={{ background: "var(--clay-100)" }}>
      <div className="sa-root" style={{ width: "100%", maxWidth: 560, padding: "24px 16px 40px", display: "flex", flexDirection: "column", gap: 20 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/art/logo.svg" alt="साथी Saathi" style={{ height: 40, width: "auto" }} />
          <LangToggle />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <h1 className="m-display hd" style={{ ["--bi-2nd" as string]: "18px" }}><Bi hi="आप कौन हैं?" en="Who are you?" /></h1>
          <p className="m-body muted"><Bi hi="डेमो में किसी एक की तरह देखें — रमेश की कहानी चारों नज़र से।" en="Step into one role — Ramesh's story from all four sides." /></p>
          <DemoBadge long />
        </div>

        {err ? <ErrorBox error={err} /> : null}
        {users.loading && <Loading />}
        {users.error ? <ErrorBox error={users.error} onRetry={users.reload} /> : null}

        <div role="list" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {users.data?.cast.map((u) => {
            const c = ROLE_CARD[u.role];
            return (
              <button key={u.id} role="listitem" type="button" className="pick" data-testid={`login-${u.role}`} disabled={busy !== null} onClick={() => go(u.id)}>
                <span className={`pick-art ${c.ground}`} style={{ width: 64, height: 64 }}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={`/art/${c.art}.webp`} alt="" />
                </span>
                <span style={{ flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
                  <span style={{ font: "700 20px/28px var(--font-display)" }}><Bi inline hi={c.hi} en={c.en} /></span>
                  <span className="m-caption">{u.name_hi ? `${u.name_hi} · ${u.name}` : u.name}</span>
                  <span className="m-caption"><Bi inline hi={c.noteHi} en={c.noteEn} /></span>
                </span>
                <Icon name="chevron-right" />
              </button>
            );
          })}
        </div>

        {process.env.NEXT_PUBLIC_DEMO_MODE === "1" && (
          <section className="sa-card" style={{ gap: 10 }}>
            <span className="m-caption" style={{ fontWeight: 600 }}><Bi inline hi="डेमो नियंत्रण" en="Demo controls" /></span>
            <button type="button" className="sa-btn sa-btn--outline" data-testid="reset-demo" disabled={busy !== null} onClick={reset}>
              <Icon name="refresh" /><Bi hi="डेमो शुरू से करें" en="Reset demo data" />
            </button>
            {resetAt && <span className="m-caption" data-testid="reset-done"><Bi inline hi="डेटा फिर से भरा गया" en="Demo data re-seeded" /></span>}
          </section>
        )}
      </div>
    </div>
  );
}
