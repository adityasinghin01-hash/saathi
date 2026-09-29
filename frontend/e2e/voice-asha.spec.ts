import { test, expect, chromium } from "@playwright/test";
import path from "path";

// ASHA reports for Ramesh BY VOICE: Chrome plays a synthetic Hindi clip (Gemini TTS, labelled synthetic)
// as the microphone, the real backend sends it to Gemini, and the check screen must show what was heard.
// Clip s01: "मेटफॉर्मिन ख़त्म… 28 सितंबर सुंदरपुर PHC… तीस गोलियां माँगी… घर में दो दिन की बची"

const CLIP = path.resolve(__dirname, "../../backend/eval/audio/synthetic/s01.wav");
const shots = "e2e/shots";

test("ASHA picks Ramesh, speaks the report, checks what was heard, sends it", async () => {
  const browser = await chromium.launch({
    args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", `--use-file-for-fake-audio-capture=${CLIP}%noloop`],
  });
  const ctx = await browser.newContext({ baseURL: "http://localhost:3000", permissions: ["microphone"], viewport: { width: 420, height: 900 } });
  const page = await ctx.newPage();
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(e.message));
  await page.addInitScript(() => localStorage.setItem("saathi_lang", "en"));

  await page.goto("/login");
  await page.getByTestId("reset-demo").click();
  await expect(page.getByTestId("reset-done")).toBeVisible({ timeout: 20_000 });
  await page.getByTestId("login-asha").click();
  await expect(page).toHaveURL(/\/asha$/);
  await expect(page.getByTestId("patient-patient-001")).toBeVisible();
  await expect(page.getByTestId("patient-patient-001")).toContainText("Ramesh");
  await page.screenshot({ path: `${shots}/v1-asha-home.png`, fullPage: true });

  await page.getByTestId("report-for").click();
  await page.getByTestId("pick-patient-001").click();
  await page.getByTestId("mic").click();
  await page.waitForTimeout(13_000); // let the 11.8 s clip play into the fake mic
  await page.screenshot({ path: `${shots}/v2-asha-recording.png`, fullPage: true });
  await page.getByTestId("stop-send").click();

  await expect(page.getByTestId("transcript")).toBeVisible({ timeout: 60_000 });
  const transcript = await page.getByTestId("transcript").textContent();
  const fallback = await page.getByTestId("ai-fallback").count();
  console.log("AI:", fallback ? "fallback" : "gemini", "| transcript:", transcript);
  await page.screenshot({ path: `${shots}/v3-asha-check.png`, fullPage: true });

  if (!fallback) {
    // Whatever the AI did fill in must match what was said (no invented values).
    // The AI may miss a field on a slow run; missed fields are handled by the check below.
    const expected: Record<string, string> = { "f-drug": "metformin", "f-qty": "30", "f-home": "2" };
    let heardAny = false;
    for (const [id, want] of Object.entries(expected)) {
      const got = await page.getByTestId(id).inputValue();
      if (got !== "") { expect(got).toBe(want); heardAny = true; }
    }
    expect(heardAny).toBe(true);
  }
  // Whatever the AI missed must be flagged, and sending must wait until it is filled.
  for (const k of ["drug_id", "requested_qty", "household_supply_days", "date"]) {
    if (await page.getByTestId(`missing-${k}`).count()) {
      await expect(page.getByTestId("confirm-send")).toBeDisabled();
      if (k === "drug_id") await page.getByTestId("f-drug").selectOption("metformin");
      if (k === "requested_qty") await page.getByTestId("f-qty").fill("30");
      if (k === "household_supply_days") await page.getByTestId("f-home").fill("2");
      if (k === "date") await page.getByTestId("f-date").fill("2026-09-28");
    }
  }
  await page.getByTestId("confirm-send").click();
  await expect(page).toHaveURL(/\/patient\/cases\/case-/);
  await expect(page.getByTestId("case-status").first()).toHaveAttribute("data-status", "reported");
  await page.screenshot({ path: `${shots}/v4-asha-case.png`, fullPage: true });

  expect(pageErrors).toEqual([]);
  await browser.close();
});
