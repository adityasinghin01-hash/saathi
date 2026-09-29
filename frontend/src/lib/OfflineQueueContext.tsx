"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { api } from "./api";

interface QueuedOp {
  op_id: string;
  method: string;
  path: string;
  body: unknown;
}

/** Split a /sync/batch reply: which queued ops are finished (sent, or already sent) and which the server refused. */
export function splitSyncResults(ops: QueuedOp[], results: { op_id: string; status: string }[]) {
  const status = new Map(results.map((r) => [r.op_id, r.status]));
  const done = ops.filter((o) => status.get(o.op_id) === "applied" || status.get(o.op_id) === "duplicate").map((o) => o.op_id);
  const failed = ops.filter((o) => status.get(o.op_id) === "error").map((o) => o.op_id);
  return { done, failed };
}

interface OfflineQueueContextType {
  isOffline: boolean;
  /** Saved reports the server refused when they were finally sent; shown to the user until dismissed. */
  failedCount: number;
  dismissFailed: () => void;
  enqueue: (op: Omit<QueuedOp, "op_id">) => Promise<string>;
  flushQueue: () => Promise<void>;
}

const OfflineQueueContext = createContext<OfflineQueueContextType | undefined>(undefined);

// Simple IndexedDB wrapper
const DB_NAME = "refill_loop_offline_queue";
const STORE_NAME = "ops";

async function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(STORE_NAME)) {
        request.result.createObjectStore(STORE_NAME, { keyPath: "op_id" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function addOp(op: QueuedOp): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).add(op);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function getOps(): Promise<QueuedOp[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const request = tx.objectStore(STORE_NAME).getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(tx.error);
  });
}

async function deleteOps(ids: string[]): Promise<void> {
  if (ids.length === 0) return;
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    ids.forEach((id) => store.delete(id));
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export function OfflineQueueProvider({ children }: { children: ReactNode }) {
  const [isOffline, setIsOffline] = useState(false);
  const isOfflineRef = React.useRef(false);
  const isFlushingRef = React.useRef(false);

  const [failedCount, setFailedCount] = useState(0);
  const dismissFailed = React.useCallback(() => setFailedCount(0), []);

  // Send what the server accepted, drop only those from the phone; refused ones are removed too
  // (they would fail the same way forever) but counted, so the user is told to report again.
  const flushRef = React.useRef<() => void>(() => {});
  const flushQueue = React.useCallback(async () => {
    if (isFlushingRef.current) return;
    isFlushingRef.current = true;
    let retry = false;
    try {
      const ops = await getOps();
      if (ops.length === 0) return;
      const { results } = await api.syncBatch(ops);
      const { done, failed } = splitSyncResults(ops, results ?? []);
      await deleteOps([...done, ...failed]);
      if (failed.length) setFailedCount((n) => n + failed.length);
    } catch (e) {
      console.error("Failed to flush offline queue", e);
      retry = true; // network may still be coming up; nothing was deleted
    } finally {
      isFlushingRef.current = false;
    }
    if (retry) setTimeout(() => { if (navigator.onLine) flushRef.current(); }, 3000);
  }, []);

  useEffect(() => { flushRef.current = flushQueue; }, [flushQueue]);

  useEffect(() => {
    const updateOnlineStatus = () => {
      const offline = typeof navigator !== "undefined" ? !navigator.onLine : false;
      isOfflineRef.current = offline;
      setIsOffline(offline);
      if (!offline) {
        flushQueue();
      }
    };

    window.addEventListener("online", updateOnlineStatus);
    window.addEventListener("offline", updateOnlineStatus);
    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        updateOnlineStatus();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);
    updateOnlineStatus(); // init

    return () => {
      window.removeEventListener("online", updateOnlineStatus);
      window.removeEventListener("offline", updateOnlineStatus);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [flushQueue]);

  const enqueue = async (opData: Omit<QueuedOp, "op_id">) => {
    const op: QueuedOp = {
      ...opData,
      op_id: crypto.randomUUID()
    };
    
    const currentlyOffline = (typeof navigator !== "undefined" && !navigator.onLine) || isOfflineRef.current || isOffline;
    if (currentlyOffline) {
      await addOp(op);
    } else {
      try {
        const { results } = await api.syncBatch([op]);
        if (splitSyncResults([op], results ?? []).failed.length) setFailedCount((n) => n + 1);
      } catch {
        await addOp(op);
      }
    }
    return op.op_id;
  };

  const effectiveOffline = isOffline || (typeof navigator !== "undefined" && !navigator.onLine);

  return (
    <OfflineQueueContext.Provider value={{ isOffline: effectiveOffline, failedCount, dismissFailed, enqueue, flushQueue }}>
      {children}
    </OfflineQueueContext.Provider>
  );
}

export function useOfflineQueue() {
  const context = useContext(OfflineQueueContext);
  if (context === undefined) {
    throw new Error("useOfflineQueue must be used within an OfflineQueueProvider");
  }
  return context;
}
