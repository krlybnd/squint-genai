"""Indexing worker settings."""

from agentic_shared.core.settings.app import AppSettings, load_app_settings
from agentic_shared.infrastructure.cache.redis.settings import RedisSettings
from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings
from agentic_shared.infrastructure.storage.minio.settings import MinioSettings
from agentic_shared.infrastructure.vector.qdrant.settings import QdrantSettings
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings
from pydantic import Field


class IndexingSettings(AppSettings):
    """Composed settings for the Celery PDF indexing worker."""

    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="PostgreSQL for document/job status updates.",
    )
    redis: RedisSettings = Field(
        default_factory=RedisSettings,
        description="Celery broker/result backend and optional cache.",
    )
    minio: MinioSettings = Field(
        default_factory=MinioSettings,
        description="Object storage source for PDF bytes to index.",
    )
    qdrant: QdrantSettings = Field(
        default_factory=QdrantSettings,
        description="Vector store target for upserted chunk points.",
    )
    llm: LiteLLMChatSettings = Field(
        default_factory=LiteLLMChatSettings,
        description="LiteLLM connection (shared proxy URL/key for embeddings path).",
    )
    embedding: LiteLLMEmbeddingSettings = Field(
        default_factory=LiteLLMEmbeddingSettings,
        description="Embedding model alias used during semantic chunking.",
    )
    index_document_task_name: str = Field(
        default="indexing.index_document",
        description="Celery task name registered for document indexing.",
    )
    index_document_max_retries: int = Field(
        default=2,
        description="Max Celery retries for a failed index_document task.",
    )
    index_document_retry_countdown: int = Field(
        default=30,
        description="Seconds to wait before retrying a failed index_document task.",
    )


def load_settings() -> IndexingSettings:
    return load_app_settings(IndexingSettings)


__all__ = ["IndexingSettings", "load_settings"]
