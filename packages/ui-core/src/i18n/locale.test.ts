import { afterEach, describe, expect, it, vi } from "vitest";
import { detectInitialLocale, localeFromI18nLanguage, setStoredLocale } from "./locale";

describe("localeFromI18nLanguage", () => {
  it("maps supported language tags", () => {
    // Arrange / Act / Assert
    expect(localeFromI18nLanguage("hu-HU")).toBe("hu");
    expect(localeFromI18nLanguage("de")).toBe("de");
  });

  it("falls back to en for unsupported tags", () => {
    // Arrange / Act
    const locale = localeFromI18nLanguage("fr-FR");

    // Assert
    expect(locale).toBe("en");
  });
});

describe("detectInitialLocale", () => {
  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("prefers a stored supported locale", () => {
    // Arrange
    setStoredLocale("de");

    // Act
    const locale = detectInitialLocale();

    // Assert
    expect(locale).toBe("de");
  });

  it("uses the browser language when nothing is stored", () => {
    // Arrange
    vi.stubGlobal("navigator", { language: "hu-HU" });

    // Act
    const locale = detectInitialLocale();

    // Assert
    expect(locale).toBe("hu");
  });

  it("falls back to en when browser language is unsupported", () => {
    // Arrange
    vi.stubGlobal("navigator", { language: "ja-JP" });

    // Act
    const locale = detectInitialLocale();

    // Assert
    expect(locale).toBe("en");
  });
});
