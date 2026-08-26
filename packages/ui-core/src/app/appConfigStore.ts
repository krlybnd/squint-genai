import type { AppFeatures, ResolvedAppConfig } from "./types";

let config: ResolvedAppConfig | null = null;

export function setAppConfig(next: ResolvedAppConfig): void {
  config = next;
}

export function getAppConfig(): ResolvedAppConfig {
  if (!config) {
    throw new Error("App config is not initialized. Call bootstrapApp first.");
  }
  return config;
}

export function getEndpoint(key: string): string {
  const value = getAppConfig().endpoints[key];
  if (!value) {
    throw new Error(`Unknown endpoint "${key}" for app "${getAppConfig().id}"`);
  }
  return value;
}

export function getAppFeatures(): AppFeatures | undefined {
  return getAppConfig().features;
}
