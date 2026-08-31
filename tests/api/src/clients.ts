import createClient, { type Client } from "openapi-fetch";

import type { AdminPaths, ApiPaths, ChatPaths } from "./generated";

export type ApiClient = Client<ApiPaths>;
export type ChatClient = Client<ChatPaths>;
export type AdminClient = Client<AdminPaths>;

/** `undefined` = env default; `null` = omit the header. */
export type ClientAuth = {
  bearer?: string | null;
  apiKey?: string | null;
  tenantId?: string | null;
};

function optionalValue(
  explicit: string | null | undefined,
  fallback: string | undefined,
): string | undefined {
  if (explicit === null) {
    return undefined;
  }
  if (explicit !== undefined) {
    const trimmed = explicit.trim();
    return trimmed || undefined;
  }
  const fromEnv = fallback?.trim();
  return fromEnv || undefined;
}

export function serviceHeaders(auth: ClientAuth = {}): Record<string, string> {
  const headers: Record<string, string> = { Accept: "application/json" };
  const bearer = optionalValue(auth.bearer, undefined);
  if (bearer) {
    headers.Authorization = `Bearer ${bearer}`;
  }
  const apiKey = optionalValue(auth.apiKey, process.env.API_KEY);
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  const tenantId = optionalValue(auth.tenantId, process.env.API_TENANT_ID);
  if (tenantId) {
    headers["X-Tenant-Id"] = tenantId;
  }
  return headers;
}

export function createApiClient(auth: ClientAuth = {}): ApiClient {
  return createClient<ApiPaths>({
    baseUrl: process.env.API_BASE_URL ?? "http://localhost:8000",
    headers: serviceHeaders(auth),
  });
}

export function createChatClient(auth: ClientAuth = {}): ChatClient {
  return createClient<ChatPaths>({
    baseUrl: process.env.CHAT_BASE_URL ?? "http://localhost:8002",
    headers: serviceHeaders(auth),
  });
}

export function createAdminClient(auth: ClientAuth = {}): AdminClient {
  return createClient<AdminPaths>({
    baseUrl: process.env.ADMIN_BASE_URL ?? "http://localhost:8003",
    headers: serviceHeaders(auth),
  });
}

export function requireData<T>(
  result: { data?: T; response: Response },
  label: string,
): T {
  if (!result.response.ok || result.data === undefined) {
    throw new Error(`${label} failed: HTTP ${result.response.status}`);
  }
  return result.data;
}
