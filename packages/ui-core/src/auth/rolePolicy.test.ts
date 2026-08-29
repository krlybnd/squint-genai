import { describe, expect, it } from "vitest";
import {
  parseKeycloakRoles,
  parseTenantIdFromClaims,
  parseTenantRolesClaim,
  resolveKeycloakRoles,
  rolePolicyHasAny,
} from "./rolePolicy";

describe("rolePolicyHasAny", () => {
  it("grants admin every requested role", () => {
    // Arrange
    const adminRoles = ["admin"];

    // Act / Assert
    expect(rolePolicyHasAny(adminRoles, "read")).toBe(true);
    expect(rolePolicyHasAny(adminRoles, "write", "read")).toBe(true);
  });

  it("matches any listed role", () => {
    // Arrange
    const readOnlyRoles = ["read"];

    // Act / Assert
    expect(rolePolicyHasAny(readOnlyRoles, "write", "read")).toBe(true);
    expect(rolePolicyHasAny(readOnlyRoles, "write")).toBe(false);
  });
});

describe("parseTenantRolesClaim", () => {
  it("parses JSON map from multivalued attribute", () => {
    expect(parseTenantRolesClaim(['{"tenant-b":["read"],"e2e":["read","write"]}'])).toEqual({
      "tenant-b": ["read"],
      e2e: ["read", "write"],
    });
  });
});

describe("resolveKeycloakRoles", () => {
  it("returns empty for missing token", () => {
    expect(resolveKeycloakRoles(undefined)).toEqual([]);
  });

  it("prefers roles for active tenant over flat realm roles", () => {
    expect(
      resolveKeycloakRoles({
        tenant_id: "tenant-b",
        roles: ["read", "write"],
        tenant_roles: ['{"tenant-b":["read"],"e2e-1":["read","write"]}'],
      }),
    ).toEqual(["read"]);
  });

  it("falls back to top-level roles when tenant_roles is absent", () => {
    expect(resolveKeycloakRoles({ roles: ["read", "write"] })).toEqual(["read", "write"]);
  });

  it("falls back to realm_access.roles", () => {
    expect(resolveKeycloakRoles({ realm_access: { roles: ["admin"] } })).toEqual(["admin"]);
  });
});

describe("parseKeycloakRoles", () => {
  it("returns empty for missing token", () => {
    expect(parseKeycloakRoles(undefined)).toEqual([]);
  });

  it("prefers top-level roles array", () => {
    expect(parseKeycloakRoles({ roles: ["read", "write"] })).toEqual(["read", "write"]);
  });

  it("falls back to realm_access.roles", () => {
    expect(parseKeycloakRoles({ realm_access: { roles: ["admin"] } })).toEqual(["admin"]);
  });

  it("returns empty when neither claim is present", () => {
    expect(parseKeycloakRoles({ sub: "u1" })).toEqual([]);
  });
});

describe("parseTenantIdFromClaims", () => {
  it("reads string tenant_id", () => {
    expect(parseTenantIdFromClaims({ tenant_id: "tenant-b" })).toBe("tenant-b");
  });
});
