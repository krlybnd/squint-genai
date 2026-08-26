import type { ComponentType, ReactNode } from "react";
import type { i18n } from "i18next";
import { authClientFromConfig } from "./authClientFromConfig";
import { mergeRuntimeAppConfig, resolveAppConfig, runtimeConfigUrl } from "./resolveAppConfig";
import { setAppConfig } from "./appConfigStore";
import { mountApp } from "./mountApp";
import type { AppConfigDefinition, RuntimeAppConfig } from "./types";

export type BootstrapAppOptions = {
  definition: AppConfigDefinition;
  i18n: i18n;
  loadApp: () => Promise<{ default: ComponentType }>;
  appCss?: string[];
};

async function loadRuntimeConfig(definition: AppConfigDefinition): Promise<RuntimeAppConfig | null> {
  const url = runtimeConfigUrl(definition);
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as RuntimeAppConfig;
  } catch {
    return null;
  }
}

export async function bootstrapApp({ definition, i18n, loadApp, appCss }: BootstrapAppOptions): Promise<void> {
  let resolved = resolveAppConfig(definition);
  const runtime = await loadRuntimeConfig(definition);
  if (runtime) {
    resolved = mergeRuntimeAppConfig(resolved, runtime);
  }
  setAppConfig(resolved);

  const { default: App } = await loadApp();
  if (appCss) {
    await Promise.all(appCss.map((href) => import(/* @vite-ignore */ href)));
  }

  await mountApp({
    authClient: authClientFromConfig(),
    i18n,
    app: <App /> as ReactNode,
    legacyApiKey: resolved.legacyApiKey,
  });
}
