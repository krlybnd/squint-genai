import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "./AuthProvider";
import { createDevAuthClient } from "./devAuthClient";
import { RequireRole } from "./RequireRole";

describe("RequireRole", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders children when the user has the role", () => {
    // Arrange
    const client = createDevAuthClient({ roles: ["read"] });

    // Act
    render(
      <AuthProvider client={client}>
        <RequireRole roles={["read"]}>
          <p>secret</p>
        </RequireRole>
      </AuthProvider>,
    );

    // Assert
    expect(screen.getByText("secret")).toBeTruthy();
  });

  it("shows deniedFallback when the user lacks the role", () => {
    // Arrange
    const client = createDevAuthClient({ roles: ["read"] });

    // Act
    render(
      <AuthProvider client={client}>
        <RequireRole roles={["admin"]} deniedFallback={<p>denied</p>}>
          <p>secret</p>
        </RequireRole>
      </AuthProvider>,
    );

    // Assert
    expect(screen.queryByText("secret")).toBeNull();
    expect(screen.getByText("denied")).toBeTruthy();
  });

  it("calls onDenied when access is missing", () => {
    // Arrange
    const onDenied = vi.fn();
    const client = createDevAuthClient({ roles: ["read"] });

    // Act
    render(
      <AuthProvider client={client}>
        <RequireRole roles={["write"]} onDenied={onDenied}>
          <p>secret</p>
        </RequireRole>
      </AuthProvider>,
    );

    // Assert
    expect(onDenied).toHaveBeenCalled();
    expect(screen.queryByText("secret")).toBeNull();
  });
});
