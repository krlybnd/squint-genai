import { rolePolicyHasAny } from "./rolePolicy";
import type { AuthClient, DevAuthConfig } from "./types";

export function createDevAuthClient(config: DevAuthConfig = {}): AuthClient {
  const username = config.username ?? "dev";
  const roles = config.roles ?? ["admin", "read", "write"];

  return {
    enabled: false,
    getUsername: () => username,
    getRoles: () => roles,
    getAccessToken: () => undefined,
    hasAnyRole(...required: string[]) {
      return rolePolicyHasAny(roles, ...required);
    },
    async refreshToken() {},
    logout() {},
    subscribe() {
      return () => {};
    },
  };
}
