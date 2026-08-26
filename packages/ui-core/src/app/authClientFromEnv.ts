import { createAuthClient, type AuthClient } from "../auth";
import type { AppConfigDefinition } from "./types";
import { resolveAppConfig } from "./resolveAppConfig";

/** @deprecated Use bootstrapApp + authClientFromConfig instead. */
export function authClientFromEnv(): AuthClient {
  const fallback: AppConfigDefinition = {
    id: "legacy",
    basePath: "/",
    devPort: 5173,
    endpoints: {},
    auth: {
      enabled: false,
      keycloakUrl: "http://localhost:8080",
      keycloakRealm: "agentic-rag-eval",
      keycloakClientId: "agentic-rag-eval-ui",
    },
  };
  const { auth } = resolveAppConfig(fallback);
  return createAuthClient({
    authEnabled: auth.enabled,
    keycloakUrl: auth.keycloakUrl,
    keycloakRealm: auth.keycloakRealm,
    keycloakClientId: auth.keycloakClientId,
  });
}
