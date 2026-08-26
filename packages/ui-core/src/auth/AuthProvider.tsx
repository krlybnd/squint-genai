import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { AuthClient } from "./types";

interface AuthState {
  client: AuthClient;
  username: string | null;
  roles: readonly string[];
  getToken: () => string | undefined;
  hasAnyRole: (...roles: string[]) => boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ client, children }: { client: AuthClient; children: ReactNode }) {
  const [, setTick] = useState(0);

  useEffect(() => {
    return client.subscribe(() => setTick((n) => n + 1));
  }, [client]);

  useEffect(() => {
    if (!client.enabled) {
      return;
    }
    const interval = window.setInterval(() => {
      void client.refreshToken().catch(() => client.logout());
    }, 30_000);
    return () => window.clearInterval(interval);
  }, [client]);

  const value: AuthState = {
    client,
    username: client.getUsername(),
    roles: client.getRoles(),
    getToken: () => client.getAccessToken(),
    hasAnyRole: (...roles) => client.hasAnyRole(...roles),
    logout: () => client.logout(),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

export function useAuthClient(): AuthClient {
  return useAuth().client;
}
