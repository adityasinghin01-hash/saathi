"use client";

import React, { useEffect } from "react";
import { useAuth } from "@/lib/AuthContext";
import { NotificationProvider } from "@/lib/NotificationContext";
import { WakeScreen } from "@/components/WakeScreen";
import { Loading } from "@/components/ui";

export function RootLayoutClient({ children }: { children: React.ReactNode }) {
  const { isLoading } = useAuth();

  useEffect(() => {
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
  }, []);

  // The wake screen also covers the login check: a returning user waits on /me while the server wakes.
  if (isLoading) return <><WakeScreen /><div className="center-page"><Loading /></div></>;
  return (
    <NotificationProvider>
      <WakeScreen />
      {children}
    </NotificationProvider>
  );
}
