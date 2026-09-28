"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { api } from "./api";

interface QueuedOp {
  op_id: string;
  method: string;
  path: string;
  body: unknown;
}

interface OfflineQueueContextType {
  isOffline: boolean;
  enqueue: (op: Omit<QueuedOp, "op_id">) => Promise<string>;
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

async function clearOps(): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).clear();
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export function OfflineQueueProvider({ children }: { children: ReactNode }) {
  const [isOffline, setIsOffline] = useState(false);

  const flushQueue = React.useCallback(async () => {
    try {
      const ops = await getOps();
      if (ops.length === 0) return;
      
      await api.syncBatch(ops);
      await clearOps();
      console.log("Offline queue flushed");
    } catch (e) {
      console.error("Failed to flush offline queue", e);
    }
  }, []);

  useEffect(() => {
    const updateOnlineStatus = () => {
      const offline = !navigator.onLine;
      setIsOffline(offline);
      if (!offline) {
        flushQueue();
      }
    };

    window.addEventListener("online", updateOnlineStatus);
    window.addEventListener("offline", updateOnlineStatus);
    updateOnlineStatus(); // init

    return () => {
      window.removeEventListener("online", updateOnlineStatus);
      window.removeEventListener("offline", updateOnlineStatus);
    };
  }, [flushQueue]);

  const enqueue = async (opData: Omit<QueuedOp, "op_id">) => {
    const op: QueuedOp = {
      ...opData,
      op_id: crypto.randomUUID()
    };
    
    if (isOffline) {
      await addOp(op);
    } else {
      // If online, just send directly? Wait, the task says "flush to /sync/batch when online".
      // Let's always try to sync directly if online.
      try {
        await api.syncBatch([op]);
      } catch {
        await addOp(op);
      }
    }
    return op.op_id;
  };

  return (
    <OfflineQueueContext.Provider value={{ isOffline, enqueue }}>
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
