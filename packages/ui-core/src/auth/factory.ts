import { createDevAuthClient } from "./devAuthClient";
import { createKeycloakAuthClient } from "./keycloakClient";
import type { AuthClient } from "./types";

export type AuthEnvConfig = {
  authEnabled: boolean;
  keycloakUrl: string;
  keycloakRealm: string;
  keycloakClientId: string;
};

export function createAuthClient(env: AuthEnvConfig): AuthClient {
  if (!env.authEnabled) {
    return createDevAuthClient();
  }
  return createKeycloakAuthClient({
    enabled: true,
    url: env.keycloakUrl,
    realm: env.keycloakRealm,
    clientId: env.keycloakClientId,
  });
}
