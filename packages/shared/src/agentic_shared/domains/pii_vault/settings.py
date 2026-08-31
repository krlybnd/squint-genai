"""Runtime toggles for vault query tokenization and SSE reveal."""

from pydantic import AliasChoices, Field

from agentic_shared.core.settings.base import EnvSettings


class PiiVaultSettings(EnvSettings):
    """Shared PII vault feature flags (query path, chat guard, SSE reveal)."""

    model_config = EnvSettings.model_config | {"populate_by_name": True}

    enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("PII_VAULT_ENABLED", "enabled"),
        description=(
            "Vault tokenizer on queries/guard + optional SSE detokenize. Env: PII_VAULT_ENABLED."
        ),
    )
    sse_detokenize_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("PII_VAULT_SSE_DETOKENIZE_ENABLED", "sse_detokenize_enabled"),
        description=(
            "Replace vault tokens with plaintext in chat SSE token + done events. "
            "Env: PII_VAULT_SSE_DETOKENIZE_ENABLED."
        ),
    )
    language: str = Field(
        default="en",
        validation_alias=AliasChoices("PII_VAULT_LANGUAGE", "language"),
        description=(
            "Presidio analyzer language for query/guard tokenization. Env: PII_VAULT_LANGUAGE."
        ),
    )


__all__ = ["PiiVaultSettings"]
