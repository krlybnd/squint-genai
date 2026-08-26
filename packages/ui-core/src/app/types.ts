export type AppAuthConfig = {
  enabled: boolean;
  keycloakUrl: string;
  keycloakRealm: string;
  keycloakClientId: string;
};

export type AppDevProxyEntry = {
  target: string;
  stripPrefix?: string;
  changeOrigin?: boolean;
};

export type AppFeatures = {
  adminPanelHref?: string;
};

export type AppConfigDefinition = {
  id: string;
  basePath: string;
  devPort: number;
  endpoints: Record<string, string>;
  devProxy?: Record<string, AppDevProxyEntry>;
  auth: AppAuthConfig;
  legacyApiKey?: string;
  features?: AppFeatures;
  runtimeConfigPath?: string;
  i18nNamespaces?: string[];
};

export type RuntimeAppConfig = {
  endpoints?: Partial<Record<string, string>>;
  auth?: Partial<AppAuthConfig>;
  legacyApiKey?: string;
  features?: Partial<AppFeatures>;
};

export type ResolvedAppConfig = AppConfigDefinition & {
  auth: AppAuthConfig;
  endpoints: Record<string, string>;
};
