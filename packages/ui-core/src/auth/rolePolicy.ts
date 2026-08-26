const ADMIN_ROLE = "admin";

export function rolePolicyHasAny(grantedRoles: readonly string[], ...required: string[]): boolean {
  const granted = new Set(grantedRoles);
  if (granted.has(ADMIN_ROLE)) {
    return true;
  }
  return required.some((role) => granted.has(role));
}

export function parseKeycloakRoles(tokenParsed: Record<string, unknown> | undefined): string[] {
  if (!tokenParsed) {
    return [];
  }
  const topLevel = tokenParsed.roles;
  if (Array.isArray(topLevel)) {
    return topLevel.map(String);
  }
  const realmAccess = tokenParsed.realm_access as { roles?: string[] } | undefined;
  return realmAccess?.roles ?? [];
}
