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
  it("leaves punctuation for React text nodes", () => {
    // Arrange
    const raw = "it's a & b\nnext";

    // Act
    const sanitized = sanitizeText(raw);

    // Assert
    expect(sanitized).toBe(raw);
  });
});
