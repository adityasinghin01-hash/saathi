import { test, expect, Page } from "@playwright/test";

const shots = "e2e/shots";

async function loginAs(page: Page, role: "patient" | "asha" | "pharmacist" | "district_officer") {
  await page.evaluate(() => localStorage.removeItem("demo_user"));
  await page.goto("/login");
  await page.getByTestId(`login-${role}`).click();
  const home = { patient: "/patient", asha: "/asha", pharmacist: "/pharmacist", district_officer: "/district" }[role];
  await expect(page).toHaveURL(new RegExp(`${home}$`));
}

test("Offline ASHA: report for Ramesh while offline, saves to phone, flushes on reconnect", async ({ page, context }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(e.message));

  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => localStorage.setItem("saathi_lang", "en"));

  // 1. Reset demo
  await page.goto("/login");
  await page.getByTestId("reset-demo").click();
  await expect(page.getByTestId("reset-done")).toBeVisible({ timeout: 20_000 });

  // 2. Log in as ASHA
  await loginAs(page, "asha");
  await expect(page.getByTestId("patient-patient-001")).toBeVisible();

  // 3. Go offline
  await context.setOffline(true);

  // 4. Report for Ramesh by typing (not voice)
  await page.getByTestId("report-for").click();
  await page.getByTestId("pick-patient-001").click();

  // Assert mic is disabled while offline and bilingual note that voice needs internet is present
  await expect(page.getByTestId("mic")).toBeDisabled();
  await expect(page.getByText("Voice needs internet")).toBeVisible();

  // Type instead
  await page.getByTestId("type-instead").click();
  await expect(page.getByTestId("f-drug")).toHaveValue("metformin");
  await page.getByTestId("f-qty").fill("30");
  await page.getByTestId("f-home").fill("0");

  // Confirm send while offline
  await page.getByTestId("confirm-send").click();

  // App must clearly say it is saved on the phone and will send when online
  await expect(page.getByTestId("saved-offline")).toBeVisible();
  await page.screenshot({ path: `${shots}/f3-offline-saved.png`, fullPage: true });

  // 5. Reconnect online
  await context.setOffline(false);

  // Wait for queue flush to complete
  await page.waitForTimeout(2000);

  // 6. Log in as pharmacist
  await loginAs(page, "pharmacist");
  await expect(page.getByTestId("count-verify")).toHaveText("1");
  const caseRows = page.locator('[data-testid^="case-row-case-"]');
  await expect(caseRows).toHaveCount(1);
  await page.screenshot({ path: `${shots}/f3-pharmacist-home.png`, fullPage: true });

  // Assert the same report does not appear twice
  await page.reload();
  await expect(page.locator('[data-testid^="case-row-case-"]')).toHaveCount(1);

  expect(pageErrors).toEqual([]);
});
