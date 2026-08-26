import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { appDirFromMeta } from "./src/build/viteAppConfig";
import { vitestNodeReportConfig } from "./src/build/vitestReportConfig";

const appDir = appDirFromMeta(import.meta.url);
const reports = vitestNodeReportConfig({ appDir, projectName: "ui-core" });

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    reporters: reports.reporters,
    coverage: {
      provider: "v8",
      include: [
        "src/auth/rolePolicy.ts",
        "src/auth/devAuthClient.ts",
        "src/auth/RequireRole.tsx",
        "src/i18n/locale.ts",
        "src/app/resolveAppConfig.ts",
        "src/utils/sanitize.ts",
        "src/preferences/themes.ts",
        "src/preferences/theme.ts",
      ],
      reportsDirectory: reports.coverage.reportsDirectory,
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
});
