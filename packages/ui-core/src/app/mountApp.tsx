import { StrictMode, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import type { i18n } from "i18next";
import { I18nextProvider } from "react-i18next";
import { AuthProvider, bootstrapAuth } from "../auth";
import { configureHttp } from "../http";
import { getAppLocaleFromInstance } from "../i18n";
import { PreferencesProvider } from "../preferences";
import { applyStoredTheme } from "../preferences/theme";
import type { AuthClient } from "../auth";

export type MountAppOptions = {
  authClient: AuthClient;
  i18n: i18n;
  app: ReactNode;
  legacyApiKey?: string;
};

export async function mountApp({ authClient, i18n, app, legacyApiKey }: MountAppOptions): Promise<void> {
  applyStoredTheme();
  await bootstrapAuth(authClient);
  configureHttp({
    authEnabled: authClient.enabled,
    getToken: () => authClient.getAccessToken(),
    refresh: () => authClient.refreshToken(),
    getLocale: () => getAppLocaleFromInstance(i18n),
    legacyApiKey,
  });

  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <I18nextProvider i18n={i18n}>
        <PreferencesProvider i18n={i18n}>
          <AuthProvider client={authClient}>{app}</AuthProvider>
        </PreferencesProvider>
      </I18nextProvider>
    </StrictMode>,
  );
}
