import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getAppConfig } from "../app/appConfigStore";
import { buildHeadersAsync } from "../http";
import { useAuth } from "./AuthProvider";

export type MembershipTenant = {
  alias: string;
  name: string;
};

export type MeResponse = {
  username: string;
  tenant_id: string | null;
  tenants: MembershipTenant[];
};

type TenantState = {
  tenantId: string | null;
  tenants: MembershipTenant[];
  tenantLabel: string;
  switching: boolean;
  switchTenant: (alias: string) => Promise<void>;
};

const TenantContext = createContext<TenantState | null>(null);

function adminBase(): string | undefined {
  return getAppConfig().endpoints.admin;
}

async function fetchMe(): Promise<MeResponse | null> {
  const base = adminBase();
  if (!base) return null;
  const res = await fetch(`${base}/v1/me`, { headers: await buildHeadersAsync(false) });
  if (!res.ok) return null;
  return (await res.json()) as MeResponse;
}

export function TenantProvider({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const [tenants, setTenants] = useState<MembershipTenant[]>([]);
  const [tenantId, setTenantId] = useState<string | null>(auth.client.getTenantId());
  const [switching, setSwitching] = useState(false);

  const reload = useCallback(async () => {
    try {
      const me = await fetchMe();
      if (!me) {
        setTenantId(auth.client.getTenantId());
        return;
      }
      setTenants(me.tenants);
      setTenantId(me.tenant_id ?? auth.client.getTenantId());
    } catch {
      setTenantId(auth.client.getTenantId());
    }
  }, [auth.client]);

  useEffect(() => {
    void reload();
  }, [reload, auth.username]);

  const switchTenant = useCallback(
    async (alias: string) => {
      const base = adminBase();
      if (!base || alias === tenantId) return;
      setSwitching(true);
      try {
        const res = await fetch(`${base}/v1/me/active-tenant`, {
          method: "PUT",
          headers: await buildHeadersAsync(),
          body: JSON.stringify({ alias }),
        });
        if (res.status === 403) {
          throw new Error("Not a member of this tenant");
        }
        if (!res.ok) {
          throw new Error(`Failed to switch tenant (${res.status})`);
        }
        const me = (await res.json()) as MeResponse;
        await auth.client.refreshToken(-1);
        setTenants(me.tenants);
        setTenantId(me.tenant_id ?? alias);
      } finally {
        setSwitching(false);
      }
    },
    [auth.client, tenantId],
  );

  const tenantLabel = useMemo(() => {
    const match = tenants.find((item) => item.alias === tenantId);
    return match?.name || tenantId || "";
  }, [tenants, tenantId]);

  const value: TenantState = {
    tenantId,
    tenants,
    tenantLabel,
    switching,
    switchTenant,
  };

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenant(): TenantState {
  const ctx = useContext(TenantContext);
  if (!ctx) {
    throw new Error("useTenant must be used within TenantProvider");
  }
  return ctx;
}
