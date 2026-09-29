// Typed client for the Saathi backend. Shapes follow docs/api-examples.md (real responses) and CONTRACT v0.5.

export type Role = "patient" | "asha" | "pharmacist" | "district_officer";
export type AiSource = "gemini" | "fake" | "fallback";

export interface Named { name: string; name_hi?: string }

export interface Facility extends Named {
  id: string;
  type: "PHC" | "CHC" | "district_store";
  block: string;
  district: string;
  lat: number;
  lng: number;
}

export interface Drug extends Named {
  id: string;
  form: string;
  strength: string;
  unit: string;
}

export interface User extends Named {
  id: string;
  role: Role;
  facility_id: string;
  patient_id?: string;
  language: "hi" | "en";
  phone_masked: string;
}

export interface Prescription {
  id: string;
  patient_id: string;
  drug_id: string;
  dose_per_day: number;
  days_supply: number;
  start_date: string;
  confirmed_by_staff: boolean;
  active: boolean;
}

export interface Patient extends Named {
  id: string;
  age: number;
  sex: string;
  conditions: string[];
  facility_id: string;
  asha_id: string;
  language: "hi" | "en";
  prescriptions: Prescription[];
  open_case?: Case | null;
}

export type CaseStatus =
  | "reported" | "verified" | "transfer_drafted" | "transfer_approved" | "dispatched" | "received"
  | "partially_supplied" | "supplied" | "closed" | "cancelled";

export interface Case {
  id: string;
  patient_id: string;
  facility_id: string;
  drug_id: string;
  requested_qty: number;
  received_qty: number;
  household_supply_days: number;
  attempted_at: string;
  reported_by: string;
  channel: "voice" | "manual";
  transcript: string | null;
  status: CaseStatus;
  verification: { result: "confirmed_stockout" | "stock_available" | "household_only" | null; on_hand: number | null; by: string | null; at: string | null };
  transfer_id: string | null;
  escalated?: boolean;
  created_at: string;
  updated_at: string;
}

export interface CaseEvent {
  id: string;
  case_id: string;
  from_status: string | null;
  to_status: string;
  actor_id: string;
  at: string;
  note: string;
}

export interface Transfer {
  id: string;
  case_id: string;
  drug_id: string;
  from_facility_id: string;
  to_facility_id: string;
  quantity: number;
  batch_ids: string[];
  batch_allocations?: { batch_id: string; quantity: number; expiry_date: string }[];
  status: "draft" | "approved" | "rejected" | "dispatched" | "received" | "cancelled";
  drafted_by: string;
  rationale: string;
  ai_source?: AiSource;
  ai_model?: string;
  constraints_checked: { donor_safety_stock_ok: boolean; expiry_ok: boolean; units_ok: boolean };
  approved_by: string | null;
  created_at: string;
}

export interface NoTransfer {
  case_id: string;
  status: "no_feasible_transfer";
  reason: string;
  ai_source?: AiSource;
}

export type CaseDetail = Case & { events: CaseEvent[]; transfer: Transfer | null };

export interface OverviewRow {
  facility_id: string;
  drug_id: string;
  on_hand: number;
  recorded_at: string;
  cohort_need: number;
  dispensing_forecast: number;
  combined: number;
  horizon_days: number;
  days_left: number;
  warning: "critical" | "low" | "ok" | null;
  open_cases: number;
  demand_rule?: string;
}

export interface Series {
  facility_id: string;
  drug_id: string;
  days: { date: string; on_hand: number; dispensed: number; stockout: boolean }[];
  cohort_need_daily: number;
  dispensing_forecast_daily: number;
  combined_daily: number;
  days_left: number;
  horizon_days: number;
}

export interface VoiceFields {
  patient_id: string;
  drug_id: string;
  requested_qty: number;
  household_supply_days: number;
  attempted_at: string;
}

/** Voice extraction: a field is null when the speaker didn't say it (CONTRACT v0.6 — never invented). */
export interface VoiceResult {
  fields: { patient_id: string; drug_id: string | null; requested_qty: number | null; household_supply_days: number | null; attempted_at: string | null };
  missing?: string[];
  not_a_refill_report?: boolean;
  transcript: string;
  ai_source: AiSource;
  ai_model?: string;
}

export interface ScenarioIds {
  patient_id: string;
  asha_id: string;
  pharmacist_id: string;
  district_officer_id: string;
  facility_id: string;
  donor_facility_id: string;
  drug_id: string;
}

export interface QueuedOp {
  op_id: string;
  method: string;
  path: string;
  body: unknown;
}

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
export const USER_KEY = "demo_user";

export class ApiError extends Error {
  constructor(public code: string, message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

function currentUser(): string | null {
  try {
    return localStorage.getItem(USER_KEY);
  } catch {
    return null;
  }
}

async function call<T>(path: string, init: RequestInit & { asUser?: string } = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const who = init.asUser ?? currentUser();
  if (who) headers.set("X-Demo-User", who);
  const res = await fetch(`${API_BASE}/api/v1${path}`, { ...init, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(data?.error?.code || String(res.status), data?.error?.message || res.statusText, res.status);
  return data as T;
}

const post = <T,>(path: string, body: unknown = {}) => call<T>(path, { method: "POST", body: JSON.stringify(body), headers: { "Idempotency-Key": crypto.randomUUID() } });

export type NotificationKind = "on_the_way" | "arrived" | "given";

export interface AppNotification {
  id: string;
  case_id: string;
  kind: NotificationKind;
  drug_id: string;
  facility_id: string;
  at: string;
  read: boolean;
  hi: string;
  en: string;
}

export const api = {
  me: async () => {
    try {
      const data = await call<User>("/me");
      try { localStorage.setItem("saathi_cache_me", JSON.stringify(data)); } catch {}
      return data;
    } catch (e) {
      try {
        const cached = localStorage.getItem("saathi_cache_me");
        if (cached) return JSON.parse(cached) as User;
      } catch {}
      throw e;
    }
  },
  demoUsers: () => call<User[]>("/demo/users"),
  scenario: () => call<ScenarioIds>("/demo/scenario/ramesh", { asUser: "officer-1" }),
  resetDemo: () => call<{ ok: boolean; seeded_at: string }>("/demo/reset", { method: "POST", asUser: "officer-1" }),
  facilities: async () => {
    try {
      const data = await call<Facility[]>("/facilities");
      try { localStorage.setItem("saathi_cache_facilities", JSON.stringify(data)); } catch {}
      return data;
    } catch (e) {
      try {
        const cached = localStorage.getItem("saathi_cache_facilities");
        if (cached) return JSON.parse(cached) as Facility[];
      } catch {}
      throw e;
    }
  },
  drugs: async () => {
    try {
      const data = await call<Drug[]>("/drugs");
      try { localStorage.setItem("saathi_cache_drugs", JSON.stringify(data)); } catch {}
      return data;
    } catch (e) {
      try {
        const cached = localStorage.getItem("saathi_cache_drugs");
        if (cached) return JSON.parse(cached) as Drug[];
      } catch {}
      throw e;
    }
  },
  patients: async () => {
    try {
      const data = await call<Patient[]>("/patients");
      try { localStorage.setItem("saathi_cache_patients", JSON.stringify(data)); } catch {}
      return data;
    } catch (e) {
      try {
        const cached = localStorage.getItem("saathi_cache_patients");
        if (cached) return JSON.parse(cached) as Patient[];
      } catch {}
      throw e;
    }
  },
  patient: async (id: string) => {
    try {
      const data = await call<Patient>(`/patients/${id}`);
      try { localStorage.setItem(`saathi_cache_patient_${id}`, JSON.stringify(data)); } catch {}
      return data;
    } catch (e) {
      try {
        const cached = localStorage.getItem(`saathi_cache_patient_${id}`);
        if (cached) return JSON.parse(cached) as Patient;
        const allCached = localStorage.getItem("saathi_cache_patients");
        if (allCached) {
          const list = JSON.parse(allCached) as Patient[];
          const found = list.find((p) => p.id === id);
          if (found) return found;
        }
      } catch {}
      throw e;
    }
  },

  cases: (params: { status?: string; facility_id?: string } = {}) => {
    const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v) as [string, string][]).toString();
    return call<Case[]>(`/cases${q ? `?${q}` : ""}`);
  },
  caseDetail: (id: string) => call<CaseDetail>(`/cases/${id}`),
  createCase: (body: Omit<VoiceFields, "patient_id"> & { patient_id: string; channel: "manual" | "voice"; transcript?: string }) => post<Case>("/cases", body),
  voice: (audio: Blob, lang: string, patientId?: string) => {
    const form = new FormData();
    form.append("audio", audio, "report.webm");
    form.append("lang", lang);
    if (patientId) form.append("patient_id", patientId); // required when an ASHA reports for a patient
    return call<VoiceResult>("/cases/voice", { method: "POST", body: form });
  },
  confirmVoice: (fields: VoiceFields, transcript: string) => post<Case>("/cases/voice/confirm", { fields, transcript }),
  verify: (id: string, result: string, on_hand: number | null) => post<Case>(`/cases/${id}/verify`, { result, on_hand }),
  supply: (id: string, quantity: number) => post<Case>(`/cases/${id}/supply`, { quantity }),
  confirmReceived: (id: string) => post<Case>(`/cases/${id}/confirm-received-by-patient`),
  cancel: (id: string, note: string) => post<Case>(`/cases/${id}/cancel`, { note }),

  stock: (facility_id?: string) => call<{ facility_id: string; drug_id: string; on_hand: number; recorded_at: string; batches: { id: string; quantity: number; expiry_date: string }[] }[]>(`/stock${facility_id ? `?facility_id=${facility_id}` : ""}`),
  postStock: (body: { facility_id: string; drug_id: string; on_hand: number; batches: { id: string; facility_id: string; drug_id: string; quantity: number; expiry_date: string }[] }) => post<unknown>("/stock", body),
  overview: (district: string) => call<OverviewRow[]>(`/district/overview?district=${encodeURIComponent(district)}`),
  series: (facility_id: string, drug_id: string, days = 60) => call<Series>(`/district/series?facility_id=${facility_id}&drug_id=${drug_id}&days=${days}`),

  transfers: (params: { status?: string; facility_id?: string } = {}) => {
    const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v) as [string, string][]).toString();
    return call<Transfer[]>(`/transfers${q ? `?${q}` : ""}`);
  },
  transfer: (id: string) => call<Transfer>(`/transfers/${id}`),
  draftTransfer: (case_id: string) => post<Transfer | NoTransfer>("/transfers/draft", { case_id }),
  approve: (id: string) => post<Transfer>(`/transfers/${id}/approve`),
  reject: (id: string, note: string) => post<Transfer>(`/transfers/${id}/reject`, { note }),
  dispatch: (id: string) => post<Transfer>(`/transfers/${id}/dispatch`),
  receive: (id: string) => post<Transfer>(`/transfers/${id}/receive`),

  syncBatch: (ops: QueuedOp[]) => call<{ results: { op_id: string; status: string }[] }>("/sync/batch", { method: "POST", body: JSON.stringify({ ops }) }),
  evaluation: () => call<Record<string, unknown>>("/evaluation/summary"),
  notifications: () => call<AppNotification[]>("/notifications"),
  markNotificationRead: (id: string) => post<{ id: string; read: true }>(`/notifications/${id}/read`),
};

export const isNoTransfer = (t: Transfer | NoTransfer): t is NoTransfer => t.status === "no_feasible_transfer";
