"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bi, DemoBadge, Icon, LangToggle, initials } from "./ui";
import { useAuth } from "@/lib/AuthContext";
import { useOfflineQueue } from "@/lib/OfflineQueueContext";
import { useLanguage } from "@/i18n/LanguageProvider";
import { useNotifications } from "@/lib/NotificationContext";
import type { Role } from "@/lib/api";

type Text = { hi: string; en: string };

const TABS: Record<"patient" | "asha" | "pharmacist", { href: string; icon: string; t: Text }[]> = {
  patient: [
    { href: "/patient", icon: "home", t: { hi: "घर", en: "Home" } },
    { href: "/patient/cases", icon: "cases", t: { hi: "शिकायतें", en: "Reports" } },
    { href: "/profile", icon: "profile", t: { hi: "प्रोफ़ाइल", en: "Profile" } },
  ],
  asha: [
    { href: "/asha", icon: "home", t: { hi: "घर", en: "Home" } },
    { href: "/patient/report", icon: "mic", t: { hi: "रिपोर्ट", en: "Report" } },
    { href: "/profile", icon: "profile", t: { hi: "प्रोफ़ाइल", en: "Profile" } },
  ],
  pharmacist: [
    { href: "/pharmacist", icon: "home", t: { hi: "घर", en: "Home" } },
    { href: "/pharmacist/stock", icon: "stock", t: { hi: "स्टॉक", en: "Stock" } },
    { href: "/profile", icon: "profile", t: { hi: "प्रोफ़ाइल", en: "Profile" } },
  ],
};

const AVATAR_CLASS: Record<Role, string> = { patient: "sa-avatar--sunk", asha: "sa-avatar--mari", pharmacist: "sa-avatar--leaf", district_officer: "" };

function OfflineBanner() {
  const { isOffline, failedCount, dismissFailed } = useOfflineQueue();
  if (failedCount > 0) {
    return (
      <div className="sa-banner sa-banner--out" role="alert" data-testid="sync-failed">
        <span className="sa-banner-ic"><Icon name="alert" /></span>
        <span style={{ flex: 1 }}>
          <Bi hi={`${failedCount} सहेजी रिपोर्ट नहीं भेजी जा सकी — कृपया दोबारा बताएँ`} en={`${failedCount} saved report could not be sent — please report it again`} />
        </span>
        <button type="button" className="sa-iconbtn" onClick={dismissFailed} data-testid="sync-failed-dismiss"><Icon name="close" /></button>
      </div>
    );
  }
  if (!isOffline) return null;
  return (
    <div className="sa-banner sa-banner--offline" role="status">
      <span className="sa-banner-ic"><Icon name="cloud-off" /></span>
      <Bi hi="ऑफ़लाइन — सहेजा गया, इंटरनेट आने पर भेजेंगे" en="Offline — saved, will send when online" />
    </div>
  );
}

/** Phone frame (patient, ASHA, pharmacist): top bar + content + tab bar. */
export function PhoneShell({ title, back, children, foot, tabs = true }: { title: Text; back?: string; children: React.ReactNode; foot?: React.ReactNode; tabs?: boolean }) {
  const { user } = useAuth();
  const { both } = useLanguage();
  const { unreadCount, openSheet } = useNotifications();
  const path = usePathname();
  const role = user?.role;
  const tabList = role && role !== "district_officer" ? TABS[role] : [];
  return (
    <div className="phone-frame">
      <div className="phone-app sa-root">
        <header className="sa-topbar" style={{ flex: "none", padding: "0 8px" }}>
          {back ? (
            <Link className="sa-iconbtn" href={back} aria-label={both("पीछे", "Back")}><Icon name="arrow-left" /></Link>
          ) : (
            <Link className="sa-avbtn" href="/profile" aria-label={both("प्रोफ़ाइल", "Profile")} style={{ padding: 4 }}>
              <span className={`sa-avatar ${role ? AVATAR_CLASS[role] : ""}`}>{initials(user?.name ?? "?")}</span>
            </Link>
          )}
          <div className="sa-topbar-title"><Bi hi={title.hi} en={title.en} /></div>
          {(role === "patient" || role === "asha") && (
            <button
              type="button"
              className="sa-iconbtn"
              data-testid="notif-bell"
              onClick={openSheet}
              aria-label={both("सूचनाएँ", "Notifications")}
              style={{ position: "relative" }}
            >
              <Icon name="notifications" />
              {unreadCount > 0 && (
                <span
                  className="sa-badge-count"
                  data-testid="notif-count"
                  style={{
                    position: "absolute",
                    top: 6,
                    right: 6,
                    minWidth: 18,
                    height: 18,
                    borderRadius: 9,
                    background: "var(--clay-600)",
                    color: "var(--on-clay)",
                    font: "600 11px/18px var(--font-sans)",
                    padding: "0 4px",
                    textAlign: "center",
                  }}
                >
                  {unreadCount}
                </span>
              )}
            </button>
          )}
          <LangToggle />
        </header>
        <OfflineBanner />
        <main>{children}</main>
        {foot && <div className="phone-foot">{foot}</div>}
        {tabs && !foot && tabList.length > 0 && (
          <nav className="sa-tabbar" aria-label={both("मुख्य", "Main")} style={{ flex: "none" }}>
            {tabList.map((tab) => (
              <Link key={tab.href} className="sa-tab" href={tab.href} aria-current={path === tab.href ? "page" : undefined}>
                <span className="sa-tab-pill"><Icon name={tab.icon} /></span>
                <Bi hi={tab.t.hi} en={tab.t.en} />
              </Link>
            ))}
          </nav>
        )}
      </div>
    </div>
  );
}

const NAV: { href: string; icon: string; t: Text }[] = [
  { href: "/district", icon: "home", t: { hi: "अवलोकन", en: "Overview" } },
  { href: "/district/transfers", icon: "transfer", t: { hi: "स्थानांतरण", en: "Transfers" } },
  { href: "/district/cases", icon: "cases", t: { hi: "मामले", en: "Cases" } },
  { href: "/district/evaluation", icon: "suggest", t: { hi: "जाँच के नतीजे", en: "Evaluation" } },
];

/** Desktop frame for the district officer: sidebar + top bar. */
export function WebShell({ title, children, actions }: { title: Text; children: React.ReactNode; actions?: React.ReactNode }) {
  const { user, logout } = useAuth();
  const { both } = useLanguage();
  const path = usePathname();
  return (
    <div className="web-app sa-root" data-audience="desk">
      <aside className="sa-sidebar">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="sa-sidebar-logo" src="/art/logo.svg" alt="साथी Saathi" />
        {NAV.map((n) => (
          <Link key={n.href} className="sa-nav" href={n.href} aria-current={(n.href === "/district" ? path === n.href || path.startsWith("/district/facility") : path.startsWith(n.href)) ? "page" : undefined}>
            <Icon name={n.icon} /><Bi hi={n.t.hi} en={n.t.en} />
          </Link>
        ))}
        <div className="sa-sidebar-foot">
          <Link className="sa-nav" href="/settings"><Icon name="settings" /><Bi hi="सेटिंग्स" en="Settings" /></Link>
          <button type="button" className="sa-nav" onClick={logout}><Icon name="logout" /><Bi hi="लॉग आउट" en="Log out" /></button>
        </div>
      </aside>
      <div className="web-main">
        <header className="sa-topbar sa-topbar--web" style={{ flex: "none" }}>
          <div className="sa-topbar-title" style={{ flex: "1 0 auto" }}><Bi hi={title.hi} en={title.en} /></div>
          {actions}
          <DemoBadge long />
          <LangToggle />
          <Link className="sa-avbtn" href="/profile" aria-label={both("प्रोफ़ाइल", "Profile")}><span className="sa-avatar">{initials(user?.name ?? "?")}</span></Link>
        </header>
        <OfflineBanner />
        <div className="web-content">{children}</div>
      </div>
    </div>
  );
}
