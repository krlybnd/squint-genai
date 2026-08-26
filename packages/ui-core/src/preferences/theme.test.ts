import { afterEach, describe, expect, it } from "vitest";
import { applyStoredTheme, getAppTheme, setAppTheme } from "./theme";

describe("theme storage", () => {
  afterEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("defaults to purple when storage is empty", () => {
    // Arrange / Act
    const theme = getAppTheme();

    // Assert
    expect(theme).toBe("purple");
  });

  it("persists and applies the selected theme", () => {
    // Arrange / Act
    setAppTheme("neptune");

    // Assert
    expect(getAppTheme()).toBe("neptune");
    expect(document.documentElement.getAttribute("data-theme")).toBe("neptune");
  });

  it("applyStoredTheme writes the current theme to the document", () => {
    // Arrange
    localStorage.setItem("app-theme", "neptune");

    // Act
    applyStoredTheme();

    // Assert
    expect(document.documentElement.getAttribute("data-theme")).toBe("neptune");
  });
});
