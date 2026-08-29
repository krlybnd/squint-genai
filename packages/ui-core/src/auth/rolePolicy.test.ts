import { describe, expect, it } from "vitest";
import { resolveKeycloakRoles, rolePolicyHasAny } from "./rolePolicy";

describe("rolePolicyHasAny", () => {
  it("grants admin every requested role", () => {
    expect(rolePolicyHasAny(["admin"], "read")).toBe(true);
    expect(rolePolicyHasAny(["admin"], "write", "read")).toBe(true);
  });

  it("matches any listed role", () => {
    expect(rolePolicyHasAny(["read"], "write", "read")).toBe(true);
    expect(rolePolicyHasAny(["read"], "write")).toBe(false);
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

  it("returns empty when neither claim is present", () => {
    expect(resolveKeycloakRoles({ sub: "u1" })).toEqual([]);
  });

  it("coerces list tenant_id", () => {
    expect(
      resolveKeycloakRoles({
        tenant_id: ["tenant-b"],
        tenant_roles: ['{"tenant-b":["read"]}'],
      }),
    ).toEqual(["read"]);
  });
});
