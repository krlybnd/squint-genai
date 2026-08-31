import { describe, expect, it } from "vitest";
import { createDevAuthClient } from "./devAuthClient";

describe("createDevAuthClient", () => {
  it("defaults to admin/read/write for local development", () => {
    // Arrange / Act
    const client = createDevAuthClient();

    // Assert
    expect(client.enabled).toBe(false);
    expect(client.getUsername()).toBe("dev");
    expect(client.hasAnyRole("admin")).toBe(true);
    expect(client.getAccessToken()).toBeUndefined();
    expect(client.getTenantId()).toBe("tenant-a");
  });

  it("honours custom username and roles", () => {
    // Arrange / Act
    const client = createDevAuthClient({ username: "alice", roles: ["read"] });

    // Assert
    expect(client.getUsername()).toBe("alice");
    expect(client.hasAnyRole("read")).toBe(true);
    expect(client.hasAnyRole("write")).toBe(false);
  });
});
