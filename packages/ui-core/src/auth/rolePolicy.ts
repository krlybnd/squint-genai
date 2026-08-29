const APP_REALM_ROLES = new Set(["admin", "read", "write"]);

export function rolePolicyHasAny(grantedRoles: readonly string[], ...required: string[]): boolean {
  const granted = new Set(grantedRoles);
  if (granted.has("admin")) {
    return true;
  }
  return required.some((role) => granted.has(role));
}

export function parseTenantIdFromClaims(
  tokenParsed: Record<string, unknown> | undefined,
): string | undefined {
  if (!tokenParsed) {
    return undefined;
  }
  const tenantId = tokenParsed.tenant_id;
  if (typeof tenantId === "string" && tenantId.trim()) {
    return tenantId.trim();
  }
  if (Array.isArray(tenantId) && tenantId.length > 0) {
    const first = tenantId[0];
    if (typeof first === "string" && first.trim()) {
      return first.trim();
    }
  }
  return undefined;
}

export function parseTenantRolesClaim(raw: unknown): Record<string, string[]> {
  if (raw == null) {
    return {};
  }
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
  const parsed: Record<string, string[]> = {};
  for (const [alias, roles] of Object.entries(payload)) {
    if (!Array.isArray(roles)) {
      continue;
    }
    const normalized = [...new Set(roles.map(String))].filter((role) => APP_REALM_ROLES.has(role)).sort();
    parsed[alias] = normalized;
  }
  return parsed;
}

export function parseKeycloakRoles(tokenParsed: Record<string, unknown> | undefined): string[] {
  if (!tokenParsed) {
    return [];
  }
  const topLevel = tokenParsed.roles;
  if (Array.isArray(topLevel)) {
    return topLevel.map(String).filter((role) => APP_REALM_ROLES.has(role));
  }
  const realmAccess = tokenParsed.realm_access as { roles?: string[] } | undefined;
  return (realmAccess?.roles ?? []).map(String).filter((role) => APP_REALM_ROLES.has(role));
}

export function resolveKeycloakRoles(tokenParsed: Record<string, unknown> | undefined): string[] {
  const tenantId = parseTenantIdFromClaims(tokenParsed);
  const tenantRoles = parseTenantRolesClaim(tokenParsed?.tenant_roles);
  if (tenantId && tenantId in tenantRoles) {
    return tenantRoles[tenantId] ?? [];
  }
  return parseKeycloakRoles(tokenParsed);
}
