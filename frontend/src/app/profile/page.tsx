"use client";

import { useAuth } from "@/lib/AuthContext";
import { useRefData } from "@/lib/hooks";
import { PhoneShell, WebShell } from "@/components/shells";
import { Bi, DemoBadge, FacilityName, Icon, LangToggle, hiName, initials } from "@/components/ui";

const ROLE: Record<string, { hi: string; en: string }> = {
  patient: { hi: "मरीज़", en: "Patient" }, asha: { hi: "आशा", en: "ASHA worker" },
  pharmacist: { hi: "फ़ार्मासिस्ट", en: "Pharmacist" }, district_officer: { hi: "ज़िला अधिकारी", en: "District officer" },
};

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const ref = useRefData();
  if (!user) return null;
  const body = (
    <>
      <section className="sa-card" style={{ alignItems: "center", gap: 10, textAlign: "center" }}>
        <span className="sa-avatar sa-avatar--lg">{initials(user.name)}</span>
        <h1 className="m-title hd"><Bi hi={hiName(user)} en={user.name} /></h1>
        <span className="m-caption"><Bi inline hi={ROLE[user.role].hi} en={ROLE[user.role].en} /> · <FacilityName f={ref.facility(user.facility_id)} id={user.facility_id} /></span>
        <span className="m-caption num">{user.phone_masked}</span>
        <DemoBadge long />
      </section>
      <section className="sa-card" style={{ gap: 12 }}>
        <span className="m-caption" style={{ fontWeight: 600 }}><Bi inline hi="कौन-सी भाषा पहले" en="Which language leads" /></span>
        <LangToggle small={false} />
        <p className="m-caption"><Bi hi="दोनों भाषाएँ हमेशा दिखेंगी" en="Both languages always show" /></p>
      </section>
      <button type="button" className="sa-btn sa-btn--outline sa-btn--block" data-testid="logout" onClick={logout}><Icon name="logout" /><Bi hi="लॉग आउट" en="Log out" /></button>
    </>
  );
  return user.role === "district_officer"
    ? <WebShell title={{ hi: "प्रोफ़ाइल", en: "Profile" }}><div style={{ maxWidth: 520, display: "flex", flexDirection: "column", gap: 16 }}>{body}</div></WebShell>
    : <PhoneShell title={{ hi: "प्रोफ़ाइल", en: "Profile" }}>{body}</PhoneShell>;
}
