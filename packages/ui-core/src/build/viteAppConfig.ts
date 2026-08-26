import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig, type UserConfig } from "vite";

export type ViteAppOptions = {
  appDir: string;
  port: number;
  base?: string;
  proxy?: Record<string, object>;
  test?: Record<string, unknown>;
};

export function viteAppConfig({ appDir, port, base, proxy, test }: ViteAppOptions): UserConfig {
  const uiCore = path.resolve(appDir, "../../packages/ui-core/src");

  return defineConfig({
    base,
    plugins: [react()],
    resolve: {
      alias: {
        "@are/ui-core": uiCore,
      },
      // Single copy so lazy-loaded app chunks share I18nextProvider context.
      dedupe: ["react", "react-dom", "i18next", "react-i18next"],
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes("node_modules/i18next") || id.includes("node_modules/react-i18next")) {
              return "i18n-vendor";
            }
          },
        },
      },
    },
    ...(test ? { test } : {}),
    server: {
      host: "0.0.0.0",
      port,
      proxy,
    },
  }) as UserConfig;
}

export function appDirFromMeta(metaUrl: string): string {
  return path.dirname(fileURLToPath(metaUrl));
}
