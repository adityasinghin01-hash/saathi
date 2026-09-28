import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  timeout: 180_000,
  workers: 1,
  use: { baseURL: "http://localhost:3000", trace: "retain-on-failure", viewport: { width: 1280, height: 900 } },
});
