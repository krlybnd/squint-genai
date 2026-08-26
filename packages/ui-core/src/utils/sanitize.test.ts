import { describe, expect, it } from "vitest";
import { escapeHtml, sanitizeText } from "./sanitize";

describe("escapeHtml", () => {
  it("escapes markup and quotes", () => {
    // Arrange
    const raw = `<script>alert("x")</script>`;

    // Act / Assert
    expect(escapeHtml(raw)).toBe("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;");
    expect(escapeHtml("a & b")).toBe("a &amp; b");
    expect(escapeHtml("it's")).toBe("it&#39;s");
  });
});

describe("sanitizeText", () => {
  it("trims then escapes", () => {
    // Arrange
    const raw = "  <b>x</b>  ";

    // Act
    const sanitized = sanitizeText(raw);

    // Assert
    expect(sanitized).toBe("&lt;b&gt;x&lt;/b&gt;");
  });
});
