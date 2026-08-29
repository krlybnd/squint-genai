import Keycloak from "keycloak-js";
import { resolveKeycloakRoles, rolePolicyHasAny } from "./rolePolicy";
import type { AuthClient, KeycloakAuthConfig } from "./types";

export function createKeycloakAuthClient(config: KeycloakAuthConfig): AuthClient {
  const keycloak = new Keycloak({
    url: config.url,
    realm: config.realm,
    clientId: config.clientId,
  });

  const listeners = new Set<() => void>();

  const notify = (): void => {
    for (const listener of listeners) {
      listener();
    }
  };

  keycloak.onAuthRefreshSuccess = notify;
  keycloak.onAuthLogout = notify;
  keycloak.onTokenExpired = () => {
    void keycloak.updateToken(30).catch(() => keycloak.logout());
  };

  return {
    enabled: config.enabled,
    getUsername() {
      if (!config.enabled) {
        return null;
      }
      return keycloak.tokenParsed?.preferred_username ?? null;
    },
    getRoles() {
      if (!config.enabled) {
        return [];
      }
      return resolveKeycloakRoles(keycloak.tokenParsed as Record<string, unknown> | undefined);
    },
    getAccessToken() {
      if (!config.enabled) {
        return undefined;
      }
      return keycloak.token ?? undefined;
    },
    hasAnyRole(...roles: string[]) {
      return rolePolicyHasAny(this.getRoles(), ...roles);
    },
    async refreshToken(minValiditySeconds = 30) {
      if (!config.enabled) {
        return;
      }
      await keycloak.updateToken(minValiditySeconds);
    },
    logout() {
      if (!config.enabled) {
        return;
      }
      void keycloak.logout({ redirectUri: window.location.origin });
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    /** @internal bootstrap only */
    async _bootstrap(): Promise<void> {
      if (!config.enabled) {
        return;
      }
      const authenticated = await keycloak.init({
        onLoad: "login-required",
        pkceMethod: "S256",
        checkLoginIframe: false,
      });
      if (!authenticated) {
        await keycloak.login();
      }
      notify();
    },
  } as AuthClient & { _bootstrap(): Promise<void> };
}

export async function bootstrapAuth(client: AuthClient): Promise<void> {
  const kc = client as AuthClient & { _bootstrap?: () => Promise<void> };
  if (kc._bootstrap) {
    await kc._bootstrap();
  }
}
