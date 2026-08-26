import { createAuthClient, type AuthClient } from "../auth";
import { getAppConfig } from "./appConfigStore";

export function authClientFromConfig(): AuthClient {
  const { auth } = getAppConfig();
  return createAuthClient({
    authEnabled: auth.enabled,
    keycloakUrl: auth.keycloakUrl,
    keycloakRealm: auth.keycloakRealm,
    keycloakClientId: auth.keycloakClientId,
  });
}
