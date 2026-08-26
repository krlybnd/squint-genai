import type { AppConfigDefinition, ResolvedAppConfig, RuntimeAppConfig } from "./types";

function envString(key: string): string | undefined {
  const value = import.meta.env[key as keyof ImportMetaEnv];
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function envBool(key: string): boolean | undefined {
  const value = envString(key);
  if (value === undefined) return undefined;
  return value === "true";
}

export function resolveAppConfig(definition: AppConfigDefinition): ResolvedAppConfig {
  const auth = {
    ...definition.auth,
    enabled: envBool("VITE_AUTH_ENABLED") ?? definition.auth.enabled,
    keycloakUrl: envString("VITE_KEYCLOAK_URL") ?? definition.auth.keycloakUrl,
    keycloakRealm: envString("VITE_KEYCLOAK_REALM") ?? definition.auth.keycloakRealm,
    keycloakClientId: envString("VITE_KEYCLOAK_CLIENT_ID") ?? definition.auth.keycloakClientId,
  };

  const endpoints: Record<string, string> = { ...definition.endpoints };
  for (const key of Object.keys(endpoints)) {
    const envKey = `VITE_${key.toUpperCase()}_URL`;
    const fromEnv = envString(envKey);
    if (fromEnv) endpoints[key] = fromEnv;
  }
  if (envString("VITE_API_URL") && "api" in endpoints) {
    endpoints.api = envString("VITE_API_URL")!;
  }
  if (envString("VITE_CHAT_URL") && "chat" in endpoints) {
    endpoints.chat = envString("VITE_CHAT_URL")!;
  }
  if (envString("VITE_ADMIN_URL") && "admin" in endpoints) {
    endpoints.admin = envString("VITE_ADMIN_URL")!;
  }

  return {
    ...definition,
    auth,
    endpoints,
    legacyApiKey: envString("VITE_API_KEY") ?? definition.legacyApiKey,
    features: { ...definition.features },
  };
}

export function mergeRuntimeAppConfig(
  base: ResolvedAppConfig,
  runtime: RuntimeAppConfig,
): ResolvedAppConfig {
  const endpoints = { ...base.endpoints };
  if (runtime.endpoints) {
    for (const [key, value] of Object.entries(runtime.endpoints)) {
      if (value !== undefined) endpoints[key] = value;
    }
  }

  return {
    ...base,
    endpoints,
    auth: { ...base.auth, ...runtime.auth },
    legacyApiKey: runtime.legacyApiKey ?? base.legacyApiKey,
    features: { ...base.features, ...runtime.features },
  };
}

export function runtimeConfigUrl(definition: AppConfigDefinition): string {
  if (definition.runtimeConfigPath) return definition.runtimeConfigPath;
  const base = definition.basePath.endsWith("/") ? definition.basePath : `${definition.basePath}/`;
  return base === "/" ? "/config.json" : `${base}config.json`;
}
