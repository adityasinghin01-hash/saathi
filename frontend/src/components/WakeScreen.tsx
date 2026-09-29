"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE } from "@/lib/api";
import { Bi, Icon } from "./ui";

export function WakeScreen() {
  const [showWake, setShowWake] = useState(false);
  const [isFading, setIsFading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const isAlreadyAwake = typeof window !== "undefined" && sessionStorage.getItem("saathi_server_awake") === "true";
  const awakeRef = useRef(isAlreadyAwake);
  const elapsedRef = useRef(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const checkHealth = useCallback(async (): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/health`, { cache: "no-store" });
      if (res.ok) {
        awakeRef.current = true;
        try { sessionStorage.setItem("saathi_server_awake", "true"); } catch {}
        return true;
      }
    } catch {
      // Still asleep or error
    }
    return false;
  }, []);

  const startPolling = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(async () => {
      elapsedRef.current += 3;
      if (elapsedRef.current >= 90) {
        setHasError(true);
        if (intervalRef.current) clearInterval(intervalRef.current);
        return;
      }
      const ok = await checkHealth();
      if (ok) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        setIsFading(true);
        setTimeout(() => {
          setShowWake(false);
          setIsFading(false);
        }, 300);
      }
    }, 3000);
  }, [checkHealth]);

  const retry = useCallback(() => {
    setHasError(false);
    elapsedRef.current = 0;
    checkHealth().then((ok) => {
      if (ok) {
        setIsFading(true);
        setTimeout(() => {
          setShowWake(false);
          setIsFading(false);
        }, 300);
      } else {
        startPolling();
      }
    });
  }, [checkHealth, startPolling]);

  useEffect(() => {
    if (awakeRef.current) return;
    let timer: NodeJS.Timeout | null = null;

    // Start 1.5s timer to show wake screen only if server hasn't answered
    timer = setTimeout(() => {
      if (!awakeRef.current) {
        setShowWake(true);
        startPolling();
      }
    }, 1500);

    // Immediate check on app start
    checkHealth().then((ok) => {
      if (ok && timer) {
        clearTimeout(timer);
      }
    });

    return () => {
      if (timer) clearTimeout(timer);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [checkHealth, startPolling]);

  if (!showWake) return null;

  return (
    <div
      className={`wake-screen${isFading ? " is-fading" : ""}`}
      data-testid="wake-screen"
      role="status"
    >
      <div
        style={{
          width: 88,
          height: 88,
          borderRadius: 24,
          background: "var(--paper-raised)",
          boxShadow: "var(--elev-2)",
          display: "grid",
          placeItems: "center",
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/art/logo.svg" alt="" width={60} height={60} style={{ objectFit: "contain" }} />
      </div>

      <div className="bi-c" style={{ display: "flex", flexDirection: "column", gap: 6, alignItems: "center", textAlign: "center" }}>
        <h1 className="m-title hd" style={{ margin: 0 }}>
          <Bi hi="सर्वर जाग रहा है…" en="Waking up the server…" />
        </h1>
        <p className="m-caption" style={{ maxWidth: 300, margin: 0 }}>
          <Bi
            hi="मुफ़्त सर्वर पर जागने में 1 मिनट तक लग सकता है"
            en="On the free server, it can take up to a minute to wake up"
          />
        </p>
      </div>

      {hasError ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 16, alignItems: "center", width: "100%", maxWidth: 360 }}>
          <div className="sa-banner sa-banner--out" role="alert" style={{ width: "100%" }}>
            <span className="sa-banner-ic"><Icon name="alert" /></span>
            <span style={{ flex: 1 }}>
              <Bi hi="सर्वर से संपर्क नहीं हो सका" en="Could not connect to the server" />
              <span className="m-caption" style={{ display: "block" }}>
                <Bi hi="कृपया फिर से कोशिश करें" en="Please try again" />
              </span>
            </span>
          </div>
          <button type="button" className="sa-btn" onClick={retry}>
            <Icon name="refresh" /><Bi hi="फिर से कोशिश करें" en="Retry" />
          </button>
        </div>
      ) : (
        <div
          style={{
            width: 220,
            height: 6,
            borderRadius: 3,
            background: "var(--paper-sunk)",
            overflow: "hidden",
            position: "relative",
            marginTop: 8,
          }}
        >
          <div className="sa-wake-bar" />
        </div>
      )}
    </div>
  );
}
