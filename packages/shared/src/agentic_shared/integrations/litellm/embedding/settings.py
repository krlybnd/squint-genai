from pydantic import Field

from agentic_shared.integrations.core.settings import IntegrationSettings


class EmbeddingSettings(IntegrationSettings):
    """Provider-agnostic embedding settings. Instantiable with defaults alone."""

    title: str = Field(
        default="embedding",
        description="Generic embedding settings title; concrete providers override.",
    )
    embedding_model: str = Field(
        default="embed",
        description="LiteLLM (or provider) model alias used for text embeddings.",
    )


class LiteLLMEmbeddingSettings(EmbeddingSettings):
    title: str = Field(
        default="litellm-embedding",
        description="Readiness/log label for the LiteLLM embedding client.",
    )
