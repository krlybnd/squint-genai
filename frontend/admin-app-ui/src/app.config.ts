import type { AppConfigDefinition } from "@are/ui-core/app/types";

export const appDefinition: AppConfigDefinition = {
  id: "admin",
  basePath: "/admin/",
  devPort: 5174,
  i18nNamespaces: ["core", "admin"],
  endpoints: {
    admin: "/admin-api",
  },
  devProxy: {
    "/admin-api": { target: "http://localhost:8003", stripPrefix: "/admin-api" },
    "/realms": { target: "http://localhost:8080" },
  },
  auth: {
    enabled: false,
    keycloakUrl: "http://localhost:8080",
    keycloakRealm: "agentic-rag-eval",
    keycloakClientId: "agentic-rag-eval-ui",
  },
  legacyApiKey: "dev-admin-key-change-me",
};
