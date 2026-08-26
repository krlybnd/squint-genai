import { describe, expect, it } from "vitest";
import { DEFAULT_THEME, isAppTheme } from "./themes";

describe("isAppTheme", () => {
  it("accepts known theme ids", () => {
    // Arrange / Act / Assert
    expect(isAppTheme("purple")).toBe(true);
    expect(isAppTheme("neptune")).toBe(true);
    expect(DEFAULT_THEME).toBe("purple");
  });

  it("rejects unknown values", () => {
    // Arrange / Act / Assert
    expect(isAppTheme("dark")).toBe(false);
    expect(isAppTheme(1)).toBe(false);
  });
});
