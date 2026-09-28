import { beforeEach, expect, test, vi } from "vitest";
import { api, ApiError } from "@/lib/api";

beforeEach(() => {
  localStorage.setItem("demo_user", "pharmacist-1");
  global.fetch = vi.fn(async () => new Response(JSON.stringify([]), { status: 200 })) as unknown as typeof fetch;
});

test("sends the demo user header", async () => {
  await api.cases({ status: "reported" });
  const [url, init] = (global.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
  expect(String(url)).toContain("/api/v1/cases?status=reported");
  expect(new Headers(init.headers).get("X-Demo-User")).toBe("pharmacist-1");
});

test("POSTs carry an Idempotency-Key", async () => {
  await api.verify("case-1", "confirmed_stockout", 0);
  const [, init] = (global.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
  expect(new Headers(init.headers).get("Idempotency-Key")).toBeTruthy();
  expect(JSON.parse(init.body)).toEqual({ result: "confirmed_stockout", on_hand: 0 });
});

test("offline sync wraps ops as {ops: [...]} (CONTRACT v0.4)", async () => {
  await api.syncBatch([{ op_id: "o1", method: "POST", path: "/cases", body: {} }]);
  const [, init] = (global.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
  expect(JSON.parse(init.body)).toEqual({ ops: [{ op_id: "o1", method: "POST", path: "/cases", body: {} }] });
});

test("backend errors become ApiError with the backend message", async () => {
  global.fetch = vi.fn(async () => new Response(JSON.stringify({ error: { code: "invalid_drug", message: "Drug is not on an active prescription" } }), { status: 422 })) as unknown as typeof fetch;
  await expect(api.createCase({ patient_id: "p", drug_id: "x", requested_qty: 1, household_supply_days: 0, attempted_at: "2026-09-28T09:00:00Z", channel: "manual" }))
    .rejects.toMatchObject({ code: "invalid_drug", status: 422 } satisfies Partial<ApiError>);
});
