import { afterEach, describe, expect, it, vi } from "vitest";
import { mergeRuntimeAppConfig, resolveAppConfig, runtimeConfigUrl } from "./resolveAppConfig";
import type { AppConfigDefinition } from "./types";

const definition: AppConfigDefinition = {
  id: "app",
  basePath: "/",
  devPort: 5173,
  endpoints: { api: "/api", chat: "/chat" },
  auth: {
    enabled: false,
    keycloakUrl: "http://kc",
    keycloakRealm: "demo",
    keycloakClientId: "app",
  },
  legacyApiKey: "legacy",
  features: {},
};

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("resolveAppConfig", () => {
  it("keeps definition defaults when env is empty", () => {
    // Arrange / Act
    const resolved = resolveAppConfig(definition);

    // Assert
    expect(resolved.auth.enabled).toBe(false);
    expect(resolved.endpoints.api).toBe("/api");
    expect(resolved.legacyApiKey).toBe("legacy");
  });

  it("overrides auth and endpoint URLs from Vite env", () => {
    // Arrange
    vi.stubEnv("VITE_AUTH_ENABLED", "true");
    vi.stubEnv("VITE_KEYCLOAK_URL", "https://idp.example");
    vi.stubEnv("VITE_API_URL", "https://api.example");

    // Act
    const resolved = resolveAppConfig(definition);

    // Assert
    expect(resolved.auth.enabled).toBe(true);
    expect(resolved.auth.keycloakUrl).toBe("https://idp.example");
    expect(resolved.endpoints.api).toBe("https://api.example");
  });
});

describe("mergeRuntimeAppConfig", () => {
  it("overlays runtime endpoints and auth flags", () => {
    // Arrange
    const base = resolveAppConfig(definition);

    // Act
    const merged = mergeRuntimeAppConfig(base, {
      endpoints: { chat: "https://chat.example" },
      auth: { enabled: true },
      legacyApiKey: "runtime-key",
    });

    // Assert
    expect(merged.endpoints.chat).toBe("https://chat.example");
    expect(merged.endpoints.api).toBe("/api");
    expect(merged.auth.enabled).toBe(true);
    expect(merged.legacyApiKey).toBe("runtime-key");
  });
});

describe("runtimeConfigUrl", () => {
  it("uses an explicit runtimeConfigPath", () => {
    // Arrange / Act
    const url = runtimeConfigUrl({ ...definition, runtimeConfigPath: "/cfg.json" });

    // Assert
    expect(url).toBe("/cfg.json");
  });

  it("derives config.json from basePath", () => {
    // Arrange / Act / Assert
    expect(runtimeConfigUrl(definition)).toBe("/config.json");
    expect(runtimeConfigUrl({ ...definition, basePath: "/admin" })).toBe("/admin/config.json");
  });
});
