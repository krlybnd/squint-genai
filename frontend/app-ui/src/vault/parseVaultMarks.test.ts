import { describe, expect, it } from "vitest";
import { parseVaultMarks, stripVaultMarks } from "./parseVaultMarks";

describe("parseVaultMarks", () => {
  it("returns plain text when there are no marks", () => {
    expect(parseVaultMarks("hello")).toEqual([{ kind: "text", value: "hello" }]);
  });

  it("splits marked vault spans from surrounding text", () => {
    const parts = parseVaultMarks(
      "Contact [[vault:<PERSON_AABBCCDD>]]Jane VaultTest[[/vault]] today.",
    );

    expect(parts).toEqual([
      { kind: "text", value: "Contact " },
      { kind: "vault", value: "Jane VaultTest", token: "<PERSON_AABBCCDD>" },
      { kind: "text", value: " today." },
    ]);
  });

  it("hides an incomplete trailing mark during streaming", () => {
    const parts = parseVaultMarks("Contact [[vault:<PERSON_AABBCCDD>]]Jane");

    expect(parts).toEqual([{ kind: "text", value: "Contact " }]);
  });

  it("strips marks for previews and comment search", () => {
    expect(
      stripVaultMarks("Ask [[vault:<PERSON_AABBCCDD>]]Jane VaultTest[[/vault]] today."),
    ).toBe("Ask Jane VaultTest today.");
  });
});
