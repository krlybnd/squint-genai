import createClient, { type Client } from "openapi-fetch";

import type { AdminPaths, ApiPaths, ChatPaths } from "./generated";

export type ApiClient = Client<ApiPaths>;
export type ChatClient = Client<ChatPaths>;
export type AdminClient = Client<AdminPaths>;

function serviceHeaders(): Record<string, string> {
  const headers: Record<string, string> = { Accept: "application/json" };
  const apiKey = process.env.API_KEY?.trim();
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  const tenantId = process.env.API_TENANT_ID?.trim();
  if (tenantId) {
    headers["X-Tenant-Id"] = tenantId;
  }
  return headers;
}

export function createApiClient(): ApiClient {
  return createClient<ApiPaths>({
    baseUrl: process.env.API_BASE_URL ?? "http://localhost:8000",
    headers: serviceHeaders(),
  });
}

export function createChatClient(): ChatClient {
  return createClient<ChatPaths>({
    baseUrl: process.env.CHAT_BASE_URL ?? "http://localhost:8002",
    headers: serviceHeaders(),
  });
}

export function createAdminClient(): AdminClient {
  return createClient<AdminPaths>({
    baseUrl: process.env.ADMIN_BASE_URL ?? "http://localhost:8003",
    headers: serviceHeaders(),
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
