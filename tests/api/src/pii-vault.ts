/** Known plaintext values embedded in tests/api/fixtures/pii-contract.pdf */
export const PII_VAULT_NAME = "Jane VaultTest";
export const PII_VAULT_EMAIL = "vault-test@example.com";
export const PII_VAULT_PDF = "pii-contract.pdf";

/** Token shape produced by index-time PII tokenization. */
export const PII_VAULT_TOKEN_PATTERN = /<[A-Z0-9_]+_[A-F0-9]{8}>/;

/** Same-tenant retrieval/SSE wraps tokens as `[[vault:<TOKEN>]]plaintext[[/vault]]`. */
const VAULT_MARK_RE =
  /\[\[vault:(<[A-Z0-9_]+_[A-F0-9]{8}>)\]\]([\s\S]*?)\[\[\/vault\]\]/g;

export type VaultMark = { token: string; value: string };

export function vaultMarks(text: string): VaultMark[] {
  return [...text.matchAll(new RegExp(VAULT_MARK_RE.source, "g"))].map((match) => ({
    token: match[1] ?? "",
    value: match[2] ?? "",
  }));
}

export function textOutsideVaultMarks(text: string): string {
  return text.replace(new RegExp(VAULT_MARK_RE.source, "g"), "");
}
