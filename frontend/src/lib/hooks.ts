"use client";

import { useCallback, useEffect, useState } from "react";
import { api, Drug, Facility } from "./api";

export interface Loaded<T> {
  data: T | undefined;
  error: unknown;
  loading: boolean;
  reload: () => void;
}

/** Load data from the API; re-runs when `key` changes. */
export function useLoad<T>(fn: () => Promise<T>, key: string): Loaded<T> {
  const [state, setState] = useState<{ data?: T; error?: unknown; loading: boolean }>({ loading: true });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let live = true;
    setState((s) => ({ ...s, loading: true })); // eslint-disable-line react-hooks/set-state-in-effect -- loading flag for a fetch
    fn()
      .then((data) => live && setState({ data, loading: false }))
      .catch((error) => live && setState({ error, loading: false }));
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` captures fn's inputs
  }, [key, tick]);
  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { data: state.data, error: state.error, loading: state.loading, reload };
}

let refCache: Promise<{ facilities: Facility[]; drugs: Drug[] }> | null = null;

/** Facilities + drugs, fetched once per page load. */
export function useRefData() {
  const r = useLoad(() => {
    refCache ??= Promise.all([api.facilities(), api.drugs()]).then(([facilities, drugs]) => ({ facilities, drugs }));
    return refCache.catch((e) => {
      refCache = null;
      throw e;
    });
  }, "ref");
  const facility = (id: string) => r.data?.facilities.find((f) => f.id === id);
  const drug = (id: string) => r.data?.drugs.find((d) => d.id === id);
  return { ...r, facility, drug };
}

/** Patient display names for staff screens (role-scoped list from GET /patients). */
export function usePatientNames() {
  const r = useLoad(() => api.patients().catch(() => []), "patient-names");
  return (id: string) => {
    const p = r.data?.find((x) => x.id === id);
    return p ? { en: `${p.name}, ${p.age}`, hi: `${p.name_hi ?? p.name}, ${p.age}`, initials: p.name } : { en: id, hi: id, initials: id };
  };
}
