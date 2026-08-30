"""Runtime toggles for vault query tokenization and SSE reveal."""

from pydantic import Field

from agentic_shared.core.settings.base import EnvSettings


class PiiVaultSettings(EnvSettings):
    """Shared PII vault feature flags (query path, chat guard, SSE reveal)."""

    enabled: bool = Field(
        default=False,
        description=(
            "Vault tokenizer on queries/guard + optional SSE detokenize. Env: PII_VAULT_ENABLED."
        ),
    )
    sse_detokenize_enabled: bool = Field(
        default=True,
        description=(
            "Replace vault tokens with plaintext in chat SSE token + done events. "
            "Env: PII_VAULT_SSE_DETOKENIZE_ENABLED."
        ),
    )
    language: str = Field(
        default="en",
        description=(
            "Presidio analyzer language for query/guard tokenization. Env: PII_VAULT_LANGUAGE."
        ),
    )


__all__ = ["PiiVaultSettings"]
