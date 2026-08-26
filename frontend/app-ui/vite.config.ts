import { appDirFromMeta, viteAppConfig } from "../../packages/ui-core/src/build/viteAppConfig";
import { devProxyFromConfig } from "../../packages/ui-core/src/build/devProxyFromConfig";
import { vitestNodeReportConfig } from "../../packages/ui-core/src/build/vitestReportConfig";
import { appDefinition } from "./src/app.config";

const appDir = appDirFromMeta(import.meta.url);
const reports = vitestNodeReportConfig({ appDir, projectName: "app-ui" });

export default viteAppConfig({
  appDir,
  port: appDefinition.devPort,
  proxy: devProxyFromConfig(appDefinition),
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    ...reports,
    coverage: {
      provider: "v8",
      include: [
        "src/features/chat/components/MessageList.tsx",
        "src/features/chat/hooks/useChatController.ts",
      ],
      reportsDirectory: reports.coverage.reportsDirectory,
      thresholds: {
        "src/features/chat/components/MessageList.tsx": {
          lines: 70,
          functions: 70,
          statements: 70,
        },
        "src/features/chat/hooks/useChatController.ts": {
          lines: 35,
          functions: 70,
          statements: 35,
        },
      },
    },
  },
});
