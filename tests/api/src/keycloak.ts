/** Password-grant helper for live JWT tests. Not an OpenAPI service client. */

export type DemoUser = {
  username: string;
  password: string;
};

const DEMO_USERS: Record<string, DemoUser> = {
  admin: { username: "admin", password: "admin" },
  "alice@tenant-a.local": { username: "alice@tenant-a.local", password: "alice" },
  "bob@tenant-b.local": { username: "bob@tenant-b.local", password: "bob" },
  "reader@tenant-a.local": { username: "reader@tenant-a.local", password: "reader" },
};

export function demoUser(who: string): DemoUser {
  const user = DEMO_USERS[who];
  if (!user) {
    throw new Error(`unknown demo user: ${who}`);
  }
  return user;
}

export function keycloakTokenUrl(): string {
  const explicit = process.env.KEYCLOAK_TOKEN_URL?.trim();
  if (explicit) {
    return explicit;
  }
  const base = (process.env.KEYCLOAK_URL ?? "http://localhost:8080").replace(/\/$/, "");
  const realm = process.env.KEYCLOAK_REALM ?? "agentic-rag-eval";
  return `${base}/realms/${realm}/protocol/openid-connect/token`;
}

export async function fetchAccessToken(who: string): Promise<string> {
  const { username, password } = demoUser(who);
  const clientId = process.env.KEYCLOAK_TOKEN_CLIENT_ID ?? "agentic-rag-eval-dev";
  const body = new URLSearchParams({
    grant_type: "password",
    client_id: clientId,
    username,
    password,
    scope: "openid tenant",
  });
  const response = await fetch(keycloakTokenUrl(), {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!response.ok) {
    throw new Error(`Keycloak token failed for ${username}: HTTP ${response.status}`);
  }
  const payload = (await response.json()) as { access_token?: string };
  if (!payload.access_token) {
    throw new Error(`Keycloak token response missing access_token for ${username}`);
  }
  return payload.access_token;
}

let cachedAdminToken: Promise<string | undefined> | undefined;

/** Admin password-grant token when Keycloak is up (`make up-auth`); otherwise undefined. */
export async function optionalAdminAccessToken(): Promise<string | undefined> {
  cachedAdminToken ??= (async () => {
    try {
      return await fetchAccessToken("admin");
    } catch {
      return undefined;
    }
  })();
  return cachedAdminToken;
}
