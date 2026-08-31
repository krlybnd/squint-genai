from pydantic import AliasChoices, Field

from agentic_shared.integrations.core.settings import IntegrationSettings


class LiteLLMRerankSettings(IntegrationSettings):
    """LiteLLM `/rerank` alias (local TEI behind the proxy)."""

    model_config = IntegrationSettings.model_config | {"populate_by_name": True}

    title: str = Field(
        default="litellm-rerank",
        description="Readiness/log label for the LiteLLM rerank client.",
    )
    rerank_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("RERANK_ENABLED", "rerank_enabled"),
        description=(
            "Call LiteLLM /rerank after hybrid RRF. Fail-open if the proxy or TEI is down. "
            "Env: RERANK_ENABLED."
        ),
    )
    rerank_model: str = Field(
        default="rerank",
        description="LiteLLM rerank alias (operations/litellm: rerank → local TEI).",
    )
    rerank_max_doc_chars: int = Field(
        default=1200,
        description=(
            "Clip each document before /rerank. MiniLM pair limit is 512 tokens; "
            "TEI returns 413 without truncate. Env: RERANK_MAX_DOC_CHARS."
        ),
    )
