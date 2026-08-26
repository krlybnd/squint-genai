"""Chat service settings."""

from agentic_shared.core.auth.settings import AuthSettings, RoleSettings
from agentic_shared.core.settings.app import AppSettings, load_app_settings
from agentic_shared.infrastructure.postgres.settings import DatabaseSettings
from agentic_shared.infrastructure.vector.settings import QdrantSettings
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.langsmith.settings import LangSmithSettings
from agentic_shared.integrations.llm.settings import LLMSettings
from agentic_shared.integrations.rerank.settings import RerankSettings
from pydantic import Field


class ChatSettings(AppSettings):
    langsmith: LangSmithSettings = Field(default_factory=LangSmithSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    rerank: RerankSettings = Field(default_factory=RerankSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    role: RoleSettings = Field(default_factory=RoleSettings)


def load_settings() -> ChatSettings:
    return load_app_settings(ChatSettings)


__all__ = ["ChatSettings", "load_settings"]
