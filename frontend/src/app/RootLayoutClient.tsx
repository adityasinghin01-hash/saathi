"use client";

import React, { useEffect } from "react";
import { useAuth } from "@/lib/AuthContext";
import { Loading } from "@/components/ui";

export function RootLayoutClient({ children }: { children: React.ReactNode }) {
  const { isLoading } = useAuth();

  useEffect(() => {
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
  }, []);

  if (isLoading) return <div className="center-page"><Loading /></div>;
  return <>{children}</>;
}
