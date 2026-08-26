"""API service settings."""

from agentic_shared.core.auth.settings import AuthSettings, RoleSettings
from agentic_shared.core.settings.app import AppSettings, load_app_settings
from agentic_shared.infrastructure.object_storage.settings import MinioSettings
from agentic_shared.infrastructure.postgres.settings import DatabaseSettings
from agentic_shared.infrastructure.redis.settings import RedisSettings
from agentic_shared.infrastructure.vector.settings import QdrantSettings
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings
from agentic_shared.integrations.rerank.settings import RerankSettings
from pydantic import Field


class ApiSettings(AppSettings):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    rerank: RerankSettings = Field(default_factory=RerankSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    minio: MinioSettings = Field(default_factory=MinioSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    role: RoleSettings = Field(default_factory=RoleSettings)


def load_settings() -> ApiSettings:
    return load_app_settings(ApiSettings)


__all__ = ["ApiSettings", "load_settings"]
