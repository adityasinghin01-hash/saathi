"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, AppNotification } from "./api";
import { useAuth } from "./AuthContext";
import { Bi, Empty, Icon, when } from "@/components/ui";
import { useLanguage } from "@/i18n/LanguageProvider";

interface NotificationContextType {
  notifications: AppNotification[];
  unreadCount: number;
  arrivedNotification: AppNotification | null;
  isSheetOpen: boolean;
  openSheet: () => void;
  closeSheet: () => void;
  markAsRead: (id: string) => Promise<void>;
  refresh: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const { both } = useLanguage();
  const router = useRouter();
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [isSheetOpen, setIsSheetOpen] = useState(false);
  const role = user?.role;
  const isRelevantRole = role === "patient" || role === "asha";

  const fetchNotifications = useCallback(async () => {
    if (!isRelevantRole) return;
    try {
      const data = await api.notifications();
      if (Array.isArray(data)) {
        setNotifications(data);
      }
    } catch {
      // Fail quietly — never crash or show error toast
    }
  }, [isRelevantRole]);

  // Poll every 20s while page is visible
  useEffect(() => {
    if (!isRelevantRole) return;

    fetchNotifications(); // eslint-disable-line react-hooks/set-state-in-effect -- initial fetch on mount

    const interval = setInterval(() => {
      if (typeof document !== "undefined" && document.visibilityState === "visible") {
        fetchNotifications();
      }
    }, 20000);

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        fetchNotifications();
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [isRelevantRole, fetchNotifications]);

  const markAsRead = useCallback(async (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
    try {
      await api.markNotificationRead(id);
    } catch {
      // Fail quietly
    }
  }, []);

  const unreadCount = useMemo(() => notifications.filter((n) => !n.read).length, [notifications]);

  const arrivedNotification = useMemo(() => {
    // Only while the medicine is waiting at the PHC: once it was given, the banner would be wrong.
    const given = new Set(notifications.filter((n) => n.kind === "given").map((n) => n.case_id));
    return notifications.find((n) => !n.read && n.kind === "arrived" && !given.has(n.case_id)) ?? null;
  }, [notifications]);

  const openSheet = useCallback(() => setIsSheetOpen(true), []);
  const closeSheet = useCallback(() => setIsSheetOpen(false), []);

  const value = useMemo(
    () => ({
      notifications,
      unreadCount,
      arrivedNotification,
      isSheetOpen,
      openSheet,
      closeSheet,
      markAsRead,
      refresh: fetchNotifications,
    }),
    [notifications, unreadCount, arrivedNotification, isSheetOpen, openSheet, closeSheet, markAsRead, fetchNotifications]
  );

  return (
    <NotificationContext.Provider value={value}>
      {children}
      {isSheetOpen && (
        <div
          className="scrim"
          style={{ position: "fixed", inset: 0, zIndex: 900, display: "flex", alignItems: "flex-end", justifyContent: "center" }}
          onClick={closeSheet}
        >
          <div
            className="sheet"
            data-testid="notif-sheet"
            style={{ width: "100%", maxWidth: 440, maxHeight: "80vh", overflowY: "auto", position: "relative" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sheet-grab" />
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0 4px" }}>
              <h2 className="m-title hd" style={{ margin: 0 }}>
                <Bi hi="सूचनाएँ" en="Notifications" />
              </h2>
              <button
                type="button"
                className="sa-iconbtn"
                data-testid="notif-close"
                onClick={closeSheet}
                aria-label={both("बंद करें", "Close")}
              >
                <Icon name="close" />
              </button>
            </div>

            {notifications.length === 0 ? (
              <Empty hi="कोई नई सूचना नहीं" en="No notifications" />
            ) : (
              <div className="sa-rows" style={{ padding: "4px 0" }}>
                {notifications.map((n) => {
                  const w = when(n.at);
                  const icName = n.kind === "arrived" ? "health-centre" : n.kind === "given" ? "hand-over" : "truck";
                  return (
                    <button
                      key={n.id}
                      type="button"
                      className={`sa-row${!n.read ? " is-unread" : ""}`}
                      data-testid={`notif-item-${n.id}`}
                      onClick={async () => {
                        await markAsRead(n.id);
                        closeSheet();
                        router.push(`/patient/cases/${n.case_id}`);
                      }}
                      style={{
                        minHeight: 72,
                        width: "100%",
                        textAlign: "left",
                        border: 0,
                        background: n.read ? "transparent" : "var(--paper-sunk)",
                        display: "flex",
                        alignItems: "flex-start",
                        gap: 12,
                        padding: "12px 14px",
                      }}
                    >
                      <span
                        className="sa-row-ic"
                        style={{
                          flex: "none",
                          background: n.kind === "arrived" ? "var(--leaf-100)" : "var(--clay-100)",
                          color: n.kind === "arrived" ? "var(--status-ok)" : "var(--clay-ink)",
                        }}
                      >
                        <Icon name={icName} size={20} />
                      </span>
                      <span className="sa-row-main" style={{ display: "flex", flexDirection: "column", gap: 2, flex: 1, minWidth: 0 }}>
                        <span style={{ font: "500 15px/22px var(--font-sans)" }}>
                          <Bi hi={n.hi} en={n.en} />
                        </span>
                        <span className="m-caption">
                          <Bi inline hi={w.hi} en={w.en} />
                        </span>
                      </span>
                      {!n.read && (
                        <span
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: "50%",
                            background: "var(--clay-600)",
                            marginTop: 6,
                            flex: "none",
                          }}
                        />
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotifications must be used within a NotificationProvider");
  }
  return context;
}
