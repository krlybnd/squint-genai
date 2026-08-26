import { defineConfig, devices } from "@playwright/test";
import { defineBddConfig } from "playwright-bdd";
import dotenv from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";

dotenv.config({ path: ".env" });

const rootDir = path.dirname(fileURLToPath(import.meta.url));
/** Repo-root .reports/e2e (HTML report + videos/traces per test). */
const e2eReportsDir = path.resolve(rootDir, "../../.reports/e2e");
const e2eArtifactsDir = path.join(e2eReportsDir, "artifacts");
const e2eHtmlReportDir = path.join(e2eReportsDir, "html");

const baseURL = process.env.E2E_BASE_URL ?? "http://localhost";
const headless = process.env.E2E_HEADED !== "1";
const slowMo = Number(process.env.E2E_SLOW_MO ?? 0);
const demoMode = process.env.E2E_HUMAN === "1" || process.env.E2E_VIDEO === "1";

export default defineConfig({
  ...defineBddConfig({
    features: "features/**/*.feature",
    steps: ["steps/**/*.steps.ts", "support/fixtures.ts"],
    outputDir: ".features-gen",
  }),
  testDir: ".features-gen",
  outputDir: e2eArtifactsDir,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ["list"],
    ["html", { outputFolder: e2eHtmlReportDir, open: "never" }],
  ],
  timeout: 120_000,
  expect: { timeout: 15_000 },
  use: {
    baseURL,
    headless,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: demoMode ? "on" : "retain-on-failure",
    launchOptions: {
      slowMo,
    },
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: { slowMo },
      },
    },
  ],
  globalSetup: "./global-setup.ts",
});
