import { appDirFromMeta, viteAppConfig } from "../../packages/ui-core/src/build/viteAppConfig";
import { devProxyFromConfig } from "../../packages/ui-core/src/build/devProxyFromConfig";
import { vitestNodeReportConfig } from "../../packages/ui-core/src/build/vitestReportConfig";
import { appDefinition } from "./src/app.config";

const appDir = appDirFromMeta(import.meta.url);
const reports = vitestNodeReportConfig({ appDir, projectName: "admin-app-ui" });

export default viteAppConfig({
  appDir,
  base: appDefinition.basePath,
  port: appDefinition.devPort,
  proxy: devProxyFromConfig(appDefinition),
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    ...reports,
    coverage: {
      provider: "v8",
      include: ["src/features/admin/AdminFormLayout.tsx"],
      reportsDirectory: reports.coverage.reportsDirectory,
      thresholds: {
        lines: 80,
        functions: 80,
        statements: 80,
      },
    },
  },
});
