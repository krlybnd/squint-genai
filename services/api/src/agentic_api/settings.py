"""API service settings."""

from agentic_shared.core.settings.app import AppSettings, load_app_settings
from agentic_shared.crosscut.auth.settings import AuthSettings, RoleSettings
from agentic_shared.crosscut.crypto.settings import CryptoSettings
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.frameworks.fastapi.defaults import FrameworkDefaults
from agentic_shared.frameworks.fastapi.settings import FastAPISettings
from agentic_shared.infrastructure.cache.redis.settings import RedisSettings
from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings
from agentic_shared.infrastructure.storage.minio.settings import MinioSettings
from agentic_shared.infrastructure.vector.qdrant.settings import QdrantSettings
from agentic_shared.integrations.litellm.analyzer.settings import AnalyzerSettings
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.guard.settings import GuardSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings
from pydantic import Field


class ApiSettings(AppSettings):
    """Composed settings for the documents / jobs / retrieval / annotations API."""

    defaults: FrameworkDefaults = Field(
        default_factory=lambda: FrameworkDefaults.from_distribution("agentic-api"),
        description="Service identity from pyproject (name / version / description).",
    )
    fastapi: FastAPISettings = Field(
        default_factory=FastAPISettings,
        description="FastAPI CORS, OpenAPI docs paths, security headers.",
    )
    llm: LiteLLMChatSettings = Field(
        default_factory=LiteLLMChatSettings,
        description="LiteLLM chat proxy (annotations moderation, etc.).",
    )
    embedding: LiteLLMEmbeddingSettings = Field(
        default_factory=LiteLLMEmbeddingSettings,
        description="LiteLLM embedding model alias used by retrieval.",
    )
    analyzer: AnalyzerSettings = Field(
        default_factory=AnalyzerSettings,
        description="Presidio analyzer for vault query tokenization on retrieval.",
    )
    guard: GuardSettings = Field(
        default_factory=GuardSettings,
        description="Prompt-injection guard API (local or vendor; compose profile guardrails).",
    )
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="PostgreSQL for documents, jobs metadata, annotations.",
    )
    redis: RedisSettings = Field(
        default_factory=RedisSettings,
        description="Redis cache and Celery broker URLs for job enqueue.",
    )
    minio: MinioSettings = Field(
        default_factory=MinioSettings,
        description="Object storage for uploaded PDF blobs.",
    )
    qdrant: QdrantSettings = Field(
        default_factory=QdrantSettings,
        description="Vector store used by the retrieval API.",
    )
    auth: AuthSettings = Field(
        default_factory=AuthSettings,
        description="Inbound request authentication (JWT / API key / none).",
    )
    role: RoleSettings = Field(
        default_factory=RoleSettings,
        description="IdP realm role → AppRole mapping for authorization.",
    )
    crypto: CryptoSettings = Field(
        default_factory=CryptoSettings,
        description="Fernet key + token salt for PII vault detokenize.",
    )
    pii_vault: PiiVaultSettings = Field(
        default_factory=PiiVaultSettings,
        description="Vault query tokenization for retrieval API.",
    )


def load_settings() -> ApiSettings:
    return load_app_settings(ApiSettings)


__all__ = ["ApiSettings", "load_settings"]
