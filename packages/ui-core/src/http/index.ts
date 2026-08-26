export type HttpConfig = {
  getToken: () => string | undefined;
  refresh: () => Promise<void>;
  getLocale: () => string;
  legacyApiKey?: string;
  authEnabled: boolean;
};

let config: HttpConfig | null = null;

export function configureHttp(next: HttpConfig): void {
  config = next;
}

export function getHttpConfig(): HttpConfig {
  if (!config) {
    throw new Error("configureHttp must be called before using buildHeaders");
  }
  return config;
}

export function buildHeaders(contentType = true): HeadersInit {
  const { getToken, getLocale, legacyApiKey, authEnabled } = getHttpConfig();
  const headers: Record<string, string> = {
    "Accept-Language": getLocale(),
  };
  if (contentType) {
    headers["Content-Type"] = "application/json";
  }
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  } else if (!authEnabled && legacyApiKey) {
    headers["X-API-Key"] = legacyApiKey;
  }
  return headers;
}

export async function buildHeadersAsync(contentType = true): Promise<HeadersInit> {
  const { refresh, authEnabled } = getHttpConfig();
  if (authEnabled) {
    try {
      await refresh();
    } catch {
      /* logout handled by AuthProvider interval */
    }
  }
  return buildHeaders(contentType);
}
