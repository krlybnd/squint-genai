"""Chat service settings."""

from agentic_shared.core.settings.app import AppSettings, load_app_settings
from agentic_shared.crosscut.auth.settings import AuthSettings, RoleSettings
from agentic_shared.crosscut.crypto.settings import CryptoSettings
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.frameworks.fastapi.defaults import FrameworkDefaults
from agentic_shared.frameworks.fastapi.settings import FastAPISettings
from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings
from agentic_shared.infrastructure.vector.qdrant.settings import QdrantSettings
from agentic_shared.integrations.litellm.analyzer.settings import AnalyzerSettings
from agentic_shared.integrations.litellm.anonymizer.settings import AnonymizerSettings
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.guard.settings import GuardSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings
from agentic_shared.integrations.litellm.rerank.settings import LiteLLMRerankSettings
from pydantic import Field

from agentic_chat.tracing import LangSmithTracingSettings


class ChatSettings(AppSettings):
    """Composed settings for LangGraph chat + SSE streaming."""

    defaults: FrameworkDefaults = Field(
        default_factory=lambda: FrameworkDefaults.from_distribution("agentic-chat"),
        description="Service identity from pyproject (name / version / description).",
    )
    fastapi: FastAPISettings = Field(
        default_factory=FastAPISettings,
        description="FastAPI CORS, OpenAPI docs paths, security headers.",
    )
    langsmith: LangSmithTracingSettings = Field(
        default_factory=LangSmithTracingSettings,
        description="Optional LangSmith tracing for LangGraph runs.",
    )
    llm: LiteLLMChatSettings = Field(
        default_factory=LiteLLMChatSettings,
        description="LiteLLM chat proxy for generate / rewrite / titles.",
    )
    embedding: LiteLLMEmbeddingSettings = Field(
        default_factory=LiteLLMEmbeddingSettings,
        description="LiteLLM embeddings for in-process retrieval.",
    )
    rerank: LiteLLMRerankSettings = Field(
        default_factory=LiteLLMRerankSettings,
        description="LiteLLM /rerank after hybrid RRF (local TEI; fail-open).",
    )
    analyzer: AnalyzerSettings = Field(
        default_factory=AnalyzerSettings,
        description="PII analyzer API (local or vendor; compose profile guardrails).",
    )
    anonymizer: AnonymizerSettings = Field(
        default_factory=AnonymizerSettings,
        description="PII anonymizer API (local or vendor; compose profile guardrails).",
    )
    guard: GuardSettings = Field(
        default_factory=GuardSettings,
        description="Prompt-injection guard API (local or vendor; compose profile guardrails).",
    )
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="PostgreSQL for chat sessions and LangGraph checkpoints.",
    )
    qdrant: QdrantSettings = Field(
        default_factory=QdrantSettings,
        description="Vector store for hybrid retrieval inside the chat graph.",
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
        description="Fernet key + token salt for PII vault reveal/detokenize.",
    )
    pii_vault: PiiVaultSettings = Field(
        default_factory=PiiVaultSettings,
        description="Vault query tokenization + SSE detokenize toggles.",
    )


def load_settings() -> ChatSettings:
    return load_app_settings(ChatSettings)


__all__ = ["ChatSettings", "load_settings"]
