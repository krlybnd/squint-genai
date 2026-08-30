/** Known plaintext values embedded in tests/api/fixtures/pii-contract.pdf */
export const PII_VAULT_NAME = "Jane VaultTest";
export const PII_VAULT_EMAIL = "vault-test@example.com";
export const PII_VAULT_PDF = "pii-contract.pdf";

/** Token shape produced by index-time PII tokenization. */
export const PII_VAULT_TOKEN_PATTERN = /<[A-Z0-9_]+_[A-F0-9]{8}>/;
