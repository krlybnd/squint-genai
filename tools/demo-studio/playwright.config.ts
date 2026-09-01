import { defineConfig, devices } from "@playwright/test";
import { defineBddConfig } from "playwright-bdd";
import dotenv from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(rootDir, "../../.env") });
dotenv.config({ path: path.resolve(rootDir, ".env") });
const reportsDir = path.resolve(rootDir, "../../.reports/demo-studio");
const recording = process.env.DEMO_RECORD === "1";
const baseURL = process.env.DEMO_BASE_URL ?? process.env.E2E_BASE_URL ?? "http://localhost";
const headless = process.env.DEMO_HEADED !== "1";
const slowMo = Number(process.env.DEMO_SLOW_MO ?? (recording ? 40 : 0));
const viewport = { width: 1920, height: 1080 };

export default defineConfig({
  ...defineBddConfig({
    features: "features/**/*.feature",
    steps: ["steps/**/*.steps.ts", "support/fixtures.ts"],
    outputDir: ".features-gen",
  }),
  testDir: ".features-gen",
  outputDir: path.join(reportsDir, "artifacts"),
  fullyParallel: false,
  retries: 0,
  workers: 1,
  maxFailures: 1,
  reporter: [
    ["list"],
    ["html", { outputFolder: path.join(reportsDir, "html"), open: "never" }],
  ],
  timeout: recording ? 1_800_000 : 360_000,
  expect: { timeout: Number(process.env.DEMO_EXPECT_TIMEOUT_MS ?? 12_000) },
  use: {
    baseURL,
    headless,
    actionTimeout: Number(process.env.DEMO_ACTION_TIMEOUT_MS ?? 15_000),
    navigationTimeout: Number(process.env.DEMO_NAV_TIMEOUT_MS ?? 20_000),
    trace: "off",
    screenshot: "only-on-failure",
    video: recording ? { mode: "on", size: viewport } : "off",
    launchOptions: { slowMo },
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport,
        launchOptions: { slowMo },
      },
    },
  ],
});
