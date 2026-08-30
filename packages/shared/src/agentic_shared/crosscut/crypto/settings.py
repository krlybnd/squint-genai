"""Encryption settings for tenant PII vault."""

from pydantic import Field

from agentic_shared.core.settings.base import EnvSettings
from agentic_shared.core.settings.secrets import SecuredStr


class CryptoSettings(EnvSettings):
    """Fernet key + HMAC salt for vault ciphertext and deterministic tokens."""

    vault_encryption_key: SecuredStr = Field(
        default=SecuredStr("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="),
        description="Fernet key (urlsafe base64, 32 bytes). Env: VAULT_ENCRYPTION_KEY.",
    )
    vault_token_salt: SecuredStr = Field(
        default=SecuredStr("dev-vault-token-salt-change-me"),
        description="HMAC salt for deterministic PII tokens. Env: VAULT_TOKEN_SALT.",
    )

    @property
    def fernet_key(self) -> bytes:
        return self.vault_encryption_key.get_secret_value().encode("ascii")

    @property
    def token_salt(self) -> str:
        return self.vault_token_salt.get_secret_value()


__all__ = ["CryptoSettings"]
