"""Indexing worker settings."""

from agentic_shared.core.settings.app import AppSettings, load_app_settings
from agentic_shared.infrastructure.object_storage.settings import MinioSettings
from agentic_shared.infrastructure.postgres.settings import DatabaseSettings
from agentic_shared.infrastructure.redis.settings import RedisSettings
from agentic_shared.infrastructure.vector.settings import QdrantSettings
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings
from pydantic import Field


class IndexingSettings(AppSettings):
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    minio: MinioSettings = Field(default_factory=MinioSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    index_document_task_name: str = "indexing.index_document"
    index_document_max_retries: int = 2
    index_document_retry_countdown: int = 30


def load_settings() -> IndexingSettings:
    return load_app_settings(IndexingSettings)


__all__ = ["IndexingSettings", "load_settings"]
