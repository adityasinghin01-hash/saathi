import { test, expect, Page } from "@playwright/test";

// The whole Ramesh story in a real browser against the real backend (DEMO_MODE=1 on :8000).
// Every step asserts what the user should see; nothing is skipped.

const API = process.env.API_BASE ?? "http://localhost:8000";
const shots = "e2e/shots";
let n = 0;
const snap = (page: Page, name: string) => page.screenshot({ path: `${shots}/${String(++n).padStart(2, "0")}-${name}.png`, fullPage: true });

async function loginAs(page: Page, role: "patient" | "asha" | "pharmacist" | "district_officer") {
  await page.evaluate(() => localStorage.removeItem("demo_user"));
  await page.goto("/login");
  await page.getByTestId(`login-${role}`).click();
  const home = { patient: "/patient", asha: "/asha", pharmacist: "/pharmacist", district_officer: "/district" }[role];
  await expect(page).toHaveURL(new RegExp(`${home}$`));
}

test("Ramesh: report → verify → AI transfer → approve → dispatch → receive → hand over → closed", async ({ page, request }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(e.message));
  await page.addInitScript(() => localStorage.setItem("saathi_lang", "en"));

  // 1. Reset the synthetic demo data
  await page.goto("/login");
  await page.getByTestId("reset-demo").click();
  await expect(page.getByTestId("reset-done")).toBeVisible();
  await snap(page, "login-reset");

  // 2. Patient reports a failed refill (typed path; voice is tested separately)
  await loginAs(page, "patient");
  await expect(page.getByTestId("not-received")).toBeVisible();
  await snap(page, "patient-home");
  await page.getByTestId("not-received").click();
  await page.getByTestId("type-instead").click();
  await expect(page.getByTestId("f-drug")).toHaveValue("metformin");
  await page.getByTestId("f-qty").fill("30");
  await page.getByTestId("f-home").fill("0");
  await snap(page, "patient-check-details");
  await page.getByTestId("confirm-send").click();
  await expect(page).toHaveURL(/\/patient\/cases\/case-/);
  const caseId = page.url().split("/").pop()!;
  await expect(page.getByTestId("case-status").first()).toHaveAttribute("data-status", "reported");
  await snap(page, "patient-case-reported");

  // 3. Pharmacist confirms the shelf is empty
  await loginAs(page, "pharmacist");
  await page.getByTestId(`case-row-${caseId}`).click();
  await expect(page).toHaveURL(new RegExp(`/pharmacist/verify/${caseId}`));
  await page.getByTestId("on-hand").fill("0");
  await page.getByTestId("result-confirmed_stockout").click();
  await snap(page, "pharmacist-verify");
  await page.getByTestId("verify-submit").click();
  await expect(page).toHaveURL(/\/pharmacist$/);
  await expect(page.getByTestId(`case-row-${caseId}`)).toHaveCount(0);

  // 4. District officer sees it and asks the engine + AI for a transfer draft
  await loginAs(page, "district_officer");
  await expect(page.getByTestId("overview-table")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("needs-action")).toBeVisible();
  await snap(page, "officer-overview");
  await page.getByTestId(`draft-${caseId}`).click();
  await expect(page).toHaveURL(/\/district\/transfers\/transfer-/, { timeout: 60_000 });
  const transferId = page.url().split("/").pop()!;
  await expect(page.getByTestId("transfer-status")).toHaveAttribute("data-status", "draft");
  await expect(page.getByTestId("rationale")).not.toBeEmpty();
  await snap(page, "officer-transfer-draft");
  await page.getByTestId("approve").click();
  await expect(page.getByTestId("transfer-status")).toHaveAttribute("data-status", "approved");
  await page.getByTestId("dispatch").click();
  await expect(page.getByTestId("transfer-status")).toHaveAttribute("data-status", "dispatched");
  await snap(page, "officer-dispatched");

  // 5. Pharmacist receives the stock and hands 30 tablets to Ramesh
  await loginAs(page, "pharmacist");
  await page.getByTestId(`incoming-${transferId}`).click();
  await page.getByTestId("mark-received").click();
  await expect(page.getByTestId("transfer-status")).toHaveAttribute("data-status", "received");
  await snap(page, "pharmacist-received");
  await page.getByTestId("go-give").click();
  await expect(page.getByTestId("give-qty")).toHaveValue("30");
  await snap(page, "pharmacist-give");
  await page.getByTestId("hand-over").click();
  await expect(page).toHaveURL(/\/pharmacist$/);

  // 6. Ramesh confirms he has his medicine → case closed
  await loginAs(page, "patient");
  await page.goto(`/patient/cases/${caseId}`);
  await expect(page.getByTestId("case-status").first()).toHaveAttribute("data-status", "supplied");
  await snap(page, "patient-supplied");
  await page.getByTestId("got-it").click();
  await expect(page.getByTestId("closed-title")).toBeVisible();
  await snap(page, "patient-closed");

  // 7. The backend agrees, and the audit trail has every step
  const res = await request.get(`${API}/api/v1/cases/${caseId}`, { headers: { "X-Demo-User": "officer-1" } });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body.status).toBe("closed");
  expect(body.events.map((e: { to_status: string }) => e.to_status)).toEqual(
    ["reported", "verified", "transfer_drafted", "transfer_approved", "dispatched", "received", "supplied", "closed"],
  );

  // 8. Officer's case board + audit drawer render the finished case
  await loginAs(page, "district_officer");
  await page.goto("/district/cases");
  await page.getByTestId(`board-${caseId}`).click();
  await expect(page.getByTestId("audit")).toBeVisible();
  await expect(page.getByTestId("audit-event")).toHaveCount(8);
  await snap(page, "officer-audit");
  await page.goto("/district/evaluation");
  await expect(page.getByTestId("sim-label")).toBeVisible();
  await snap(page, "officer-evaluation");

  expect(pageErrors).toEqual([]);
});
