import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AdminFormField, AdminFormGrid, AdminFormSection } from "./AdminFormLayout";

describe("AdminFormSection", () => {
  it("renders title, description, and children", () => {
    // Arrange / Act
    render(
      <AdminFormSection title="Tenant" description="Core tenant fields">
        <p>child</p>
      </AdminFormSection>,
    );

    // Assert
    expect(screen.getByRole("heading", { name: "Tenant" })).toBeTruthy();
    expect(screen.getByText("Core tenant fields")).toBeTruthy();
    expect(screen.getByText("child")).toBeTruthy();
  });
});

describe("AdminFormGrid", () => {
  it("applies the requested column layout", () => {
    // Arrange / Act
    const { container } = render(
      <AdminFormGrid columns={1}>
        <span>a</span>
      </AdminFormGrid>,
    );

    // Assert
    expect(container.firstElementChild?.className).toContain("cols-1");
  });
});

describe("AdminFormField", () => {
  it("renders editable children with label and hint", () => {
    // Arrange / Act
    render(
      <AdminFormField id="name" label="Name" hint="Required">
        <input id="name" defaultValue="Acme" />
      </AdminFormField>,
    );

    // Assert
    expect(screen.getByLabelText("Name")).toBeTruthy();
    expect(screen.getByText("Required")).toBeTruthy();
  });

  it("renders read-only values with an em dash fallback", () => {
    // Arrange / Act
    render(<AdminFormField id="slug" label="Slug" readOnlyValue="" />);

    // Assert
    expect(screen.getByText("—")).toBeTruthy();
  });
});
