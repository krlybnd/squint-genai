export type AuthClient = {
  readonly enabled: boolean;
  getUsername(): string | null;
  getRoles(): readonly string[];
  getAccessToken(): string | undefined;
  hasAnyRole(...roles: string[]): boolean;
  refreshToken(minValiditySeconds?: number): Promise<void>;
  logout(): void;
  subscribe(listener: () => void): () => void;
};

export type KeycloakAuthConfig = {
  enabled: boolean;
  url: string;
  realm: string;
  clientId: string;
};

export type DevAuthConfig = {
  username?: string;
  roles?: readonly string[];
};
