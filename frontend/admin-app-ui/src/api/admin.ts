import { adminBase, buildHeadersAsync } from "./http";

export type Tenant = {
  id: string;
  alias: string;
  name: string;
  enabled: boolean;
};

export type User = {
  id: string;
  username: string;
  email: string | null;
  enabled: boolean;
  tenant_id: string | null;
  tenant_ids: string[];
  realm_roles: string[];
};

export type TenantMember = {
  id: string;
  username: string;
  email: string | null;
};

export type AdminPage<T> = {
  items: T[];
  first: number;
  max: number;
  has_more: boolean;
};

function buildPageQuery(params: { search?: string; first?: number; max?: number }): string {
  const q = new URLSearchParams();
  if (params.search?.trim()) q.set("search", params.search.trim());
  if (params.first != null) q.set("first", String(params.first));
  if (params.max != null) q.set("max", String(params.max));
  const s = q.toString();
  return s ? `?${s}` : "";
}

export async function fetchTenants(): Promise<Tenant[]> {
  const res = await fetch(`${adminBase()}/v1/tenants`, { headers: await buildHeadersAsync(false) });
  if (!res.ok) throw new Error(`Failed to list tenants (${res.status})`);
  const data = (await res.json()) as { items: Tenant[] };
  return data.items ?? [];
}

export async function createTenant(alias: string, name: string): Promise<Tenant> {
  const res = await fetch(`${adminBase()}/v1/tenants`, {
    method: "POST",
    headers: await buildHeadersAsync(),
    body: JSON.stringify({ alias, name }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Failed to create tenant (${res.status})${detail ? `: ${detail}` : ""}`);
  }
  return res.json() as Promise<Tenant>;
}

export async function updateTenant(alias: string, body: { name: string; enabled: boolean }): Promise<Tenant> {
  const res = await fetch(`${adminBase()}/v1/tenants/${encodeURIComponent(alias)}`, {
    method: "PATCH",
    headers: await buildHeadersAsync(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Failed to update tenant (${res.status})${detail ? `: ${detail}` : ""}`);
  }
  return res.json() as Promise<Tenant>;
}

export async function deleteTenant(alias: string): Promise<void> {
  const res = await fetch(`${adminBase()}/v1/tenants/${encodeURIComponent(alias)}`, {
    method: "DELETE",
    headers: await buildHeadersAsync(false),
  });
  if (!res.ok) throw new Error(`Failed to delete tenant (${res.status})`);
}

export async function fetchTenantMembersPage(
  alias: string,
  params: { first?: number; max?: number } = {},
): Promise<AdminPage<TenantMember>> {
  const qs = buildPageQuery({ first: params.first ?? 0, max: params.max ?? 50 });
  const res = await fetch(`${adminBase()}/v1/tenants/${encodeURIComponent(alias)}/members${qs}`, {
    headers: await buildHeadersAsync(false),
  });
  if (!res.ok) throw new Error(`Failed to list tenant members (${res.status})`);
  return res.json() as Promise<AdminPage<TenantMember>>;
}

export async function fetchTenantMembers(alias: string): Promise<TenantMember[]> {
  const all: TenantMember[] = [];
  let first = 0;
  const max = 200;
  for (;;) {
    const page = await fetchTenantMembersPage(alias, { first, max });
    all.push(...page.items);
    if (!page.has_more) break;
    first += page.items.length;
  }
  return all;
}

export async function addTenantMember(alias: string, username: string): Promise<TenantMember> {
  const res = await fetch(`${adminBase()}/v1/tenants/${encodeURIComponent(alias)}/members`, {
    method: "POST",
    headers: await buildHeadersAsync(),
    body: JSON.stringify({ username }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Failed to add member (${res.status})${detail ? `: ${detail}` : ""}`);
  }
  return res.json() as Promise<TenantMember>;
}

export async function removeTenantMember(alias: string, username: string): Promise<void> {
  const res = await fetch(
    `${adminBase()}/v1/tenants/${encodeURIComponent(alias)}/members/${encodeURIComponent(username)}`,
    {
      method: "DELETE",
      headers: await buildHeadersAsync(false),
    },
  );
  if (!res.ok) throw new Error(`Failed to remove member (${res.status})`);
}

export async function fetchUsersPage(
  params: { search?: string; first?: number; max?: number } = {},
): Promise<AdminPage<User>> {
  const qs = buildPageQuery({
    search: params.search,
    first: params.first ?? 0,
    max: params.max ?? 50,
  });
  const res = await fetch(`${adminBase()}/v1/users${qs}`, { headers: await buildHeadersAsync(false) });
  if (!res.ok) throw new Error(`Failed to list users (${res.status})`);
  return res.json() as Promise<AdminPage<User>>;
}

export async function fetchUsers(search?: string): Promise<User[]> {
  const all: User[] = [];
  let first = 0;
  const max = 200;
  for (;;) {
    const page = await fetchUsersPage({ search, first, max });
    all.push(...page.items);
    if (!page.has_more) break;
    first += page.items.length;
  }
  return all;
}

export async function fetchUser(username: string): Promise<User> {
  const res = await fetch(`${adminBase()}/v1/users/${encodeURIComponent(username)}`, {
    headers: await buildHeadersAsync(false),
  });
  if (!res.ok) throw new Error(`Failed to load user (${res.status})`);
  return res.json() as Promise<User>;
}

export async function createUser(input: {
  username: string;
  email?: string;
  password: string;
  realm_roles: string[];
}): Promise<User> {
  const res = await fetch(`${adminBase()}/v1/users`, {
    method: "POST",
    headers: await buildHeadersAsync(),
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Failed to create user (${res.status})${detail ? `: ${detail}` : ""}`);
  }
  return res.json() as Promise<User>;
}

export async function updateUser(
  username: string,
  body: {
    email?: string | null;
    enabled?: boolean;
    realm_roles?: string[];
    tenant_id?: string;
    password?: string;
  },
): Promise<User> {
  const res = await fetch(`${adminBase()}/v1/users/${encodeURIComponent(username)}`, {
    method: "PATCH",
    headers: await buildHeadersAsync(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Failed to update user (${res.status})${detail ? `: ${detail}` : ""}`);
  }
  return res.json() as Promise<User>;
}

export async function assignUserTenant(
  username: string,
  alias: string,
  options?: { setActive?: boolean },
): Promise<User> {
  const res = await fetch(`${adminBase()}/v1/users/${encodeURIComponent(username)}/tenant`, {
    method: "POST",
    headers: await buildHeadersAsync(),
    body: JSON.stringify({
      alias,
      set_active: options?.setActive,
    }),
  });
  if (!res.ok) throw new Error(`Failed to assign tenant (${res.status})`);
  return res.json() as Promise<User>;
}

export async function setActiveUserTenant(username: string, alias: string): Promise<User> {
  const res = await fetch(`${adminBase()}/v1/users/${encodeURIComponent(username)}/active-tenant`, {
    method: "PUT",
    headers: await buildHeadersAsync(),
    body: JSON.stringify({ alias }),
  });
  if (!res.ok) throw new Error(`Failed to set active tenant (${res.status})`);
  return res.json() as Promise<User>;
}

export async function removeUserFromTenant(username: string, alias: string): Promise<User> {
  const res = await fetch(
    `${adminBase()}/v1/users/${encodeURIComponent(username)}/tenants/${encodeURIComponent(alias)}`,
    {
      method: "DELETE",
      headers: await buildHeadersAsync(false),
    },
  );
  if (!res.ok) throw new Error(`Failed to remove tenant (${res.status})`);
  return res.json() as Promise<User>;
}

export async function removeUserTenant(username: string): Promise<User> {
  const res = await fetch(`${adminBase()}/v1/users/${encodeURIComponent(username)}/tenant`, {
    method: "DELETE",
    headers: await buildHeadersAsync(false),
  });
  if (!res.ok) throw new Error(`Failed to remove tenant (${res.status})`);
  return res.json() as Promise<User>;
}
