"""LiteLLM embedding integration."""

from agentic_shared.integrations.litellm.embedding.client import LiteLLMEmbeddingClient
from agentic_shared.integrations.litellm.embedding.protocols import EmbeddingClient
from agentic_shared.integrations.litellm.embedding.settings import (
    EmbeddingSettings,
    LiteLLMEmbeddingSettings,
)

__all__ = [
    "EmbeddingClient",
    "EmbeddingSettings",
    "LiteLLMEmbeddingClient",
    "LiteLLMEmbeddingSettings",
]
