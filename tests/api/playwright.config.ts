import { defineConfig } from "@playwright/test";
import { defineBddConfig } from "playwright-bdd";
import dotenv from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";

dotenv.config({ path: ".env" });

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const reportsDir = path.resolve(rootDir, "../../.reports/api");

const testDir = defineBddConfig({
  features: "features/**/*.feature",
  steps: ["steps/**/*.steps.ts", "support/fixtures.ts"],
  outputDir: ".features-gen",
});

export default defineConfig({
  testDir,
  outputDir: path.join(reportsDir, "artifacts"),
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [
    ["list"],
    ["html", { outputFolder: path.join(reportsDir, "html"), open: "never" }],
  ],
  timeout: 30_000,
  expect: { timeout: 10_000 },
  projects: [{ name: "api" }],
});
