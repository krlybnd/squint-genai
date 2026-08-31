import type { AppConfigDefinition } from "@are/ui-core/app/types";

export const appDefinition: AppConfigDefinition = {
  id: "app",
  basePath: "/",
  devPort: 5173,
  i18nNamespaces: ["core", "app"],
  endpoints: {
    api: "/api",
    chat: "/chat",
    admin: "/admin-api",
  },
  devProxy: {
    "/api": { target: "http://localhost:8000", stripPrefix: "/api" },
    "/chat": { target: "http://localhost:8002", stripPrefix: "/chat" },
    "/admin-api": { target: "http://localhost:8003", stripPrefix: "/admin-api" },
    "/admin": { target: "http://localhost:5174" },
    "/realms": { target: "http://localhost:8080" },
  },
  auth: {
    enabled: false,
    keycloakUrl: "http://localhost:8080",
    keycloakRealm: "agentic-rag-eval",
    keycloakClientId: "agentic-rag-eval-ui",
  },
  legacyApiKey: "dev-admin-key-change-me",
  features: {
    adminPanelHref: "/admin/",
  },
};
