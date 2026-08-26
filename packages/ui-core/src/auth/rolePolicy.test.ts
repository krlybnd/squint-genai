import { describe, expect, it } from "vitest";
import { parseKeycloakRoles, rolePolicyHasAny } from "./rolePolicy";

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

describe("parseKeycloakRoles", () => {
  it("returns empty for missing token", () => {
    // Arrange / Act
    const roles = parseKeycloakRoles(undefined);

    // Assert
    expect(roles).toEqual([]);
  });

  it("prefers top-level roles array", () => {
    // Arrange / Act
    const roles = parseKeycloakRoles({ roles: ["read", "write"] });

    // Assert
    expect(roles).toEqual(["read", "write"]);
  });

  it("falls back to realm_access.roles", () => {
    // Arrange / Act
    const roles = parseKeycloakRoles({ realm_access: { roles: ["admin"] } });

    // Assert
    expect(roles).toEqual(["admin"]);
  });

  it("returns empty when neither claim is present", () => {
    // Arrange / Act
    const roles = parseKeycloakRoles({ sub: "u1" });

    // Assert
    expect(roles).toEqual([]);
  });
});
