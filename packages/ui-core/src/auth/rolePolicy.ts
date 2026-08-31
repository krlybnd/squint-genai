const APP_ROLES = new Set(["admin", "read", "write"]);

export function rolePolicyHasAny(grantedRoles: readonly string[], ...required: string[]): boolean {
  const granted = new Set(grantedRoles);
  if (granted.has("admin")) {
    return true;
  }
  return required.some((role) => granted.has(role));
}

/** Effective app roles from Keycloak token: tenant_roles[tenant_id] else flat roles. */
export function resolveKeycloakRoles(tokenParsed: Record<string, unknown> | undefined): string[] {
  if (!tokenParsed) {
    return [];
  }
  const tenantId = tenantIdFrom(tokenParsed.tenant_id);
  const byTenant = tenantRolesFrom(tokenParsed.tenant_roles);
  if (tenantId && tenantId in byTenant) {
    return byTenant[tenantId] ?? [];
  }
  return flatRolesFrom(tokenParsed);
}

/** @deprecated Prefer resolveKeycloakRoles — kept for existing imports. */
export function parseKeycloakRoles(tokenParsed: Record<string, unknown> | undefined): string[] {
  return resolveKeycloakRoles(tokenParsed);
}

export function tenantIdFrom(value: unknown): string | undefined {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  if (Array.isArray(value) && typeof value[0] === "string" && value[0].trim()) {
    return value[0].trim();
  }
  return undefined;
}

function tenantRolesFrom(raw: unknown): Record<string, string[]> {
  let payload: unknown = raw;
  if (Array.isArray(raw) && raw.length > 0) {
    payload = raw[0];
  }
  if (typeof payload === "string") {
    try {
      payload = JSON.parse(payload);
    } catch {
      return {};
    }
  }
  if (typeof payload !== "object" || payload === null || Array.isArray(payload)) {
    return {};
  }
  const out: Record<string, string[]> = {};
  for (const [alias, roles] of Object.entries(payload)) {
    if (!Array.isArray(roles)) {
      continue;
    }
    out[alias] = [...new Set(roles.map(String).filter((role) => APP_ROLES.has(role)))].sort();
  }
  return out;
}

function flatRolesFrom(tokenParsed: Record<string, unknown>): string[] {
  const topLevel = tokenParsed.roles;
  if (Array.isArray(topLevel)) {
    return topLevel.map(String).filter((role) => APP_ROLES.has(role));
  }
  const realmAccess = tokenParsed.realm_access as { roles?: string[] } | undefined;
  return (realmAccess?.roles ?? []).map(String).filter((role) => APP_ROLES.has(role));
}
