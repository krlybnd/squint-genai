"""Live eval suite settings: host SUT endpoints and corpus-specific generation overrides."""

from __future__ import annotations

from pathlib import Path

from agentic_chat.core.deps import AgentGraphDeps
from agentic_shared.core.settings.base import EnvSettings
from agentic_shared.domains.retrieval.factory import create_async_retrieval_service
from agentic_shared.infrastructure.vector.settings import QdrantSettings
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm import OpenAIChatClient
from agentic_shared.integrations.llm.settings import LLMSettings
from agentic_shared.integrations.rerank.settings import RerankSettings
from pydantic import AliasChoices, Field
from pydantic_settings import SettingsConfigDict

from agentic_eval.modules.generation.settings import GenerationSettings
from agentic_eval.settings import EVAL_ROOT, EvalSettings


class SutSettings(EnvSettings):
    """Services the live eval process talks to. Defaults are published compose ports."""

    model_config = SettingsConfigDict(
        env_prefix="EVAL_SUT_",
        extra="ignore",
        env_file=None,
        populate_by_name=True,
        env_ignore_empty=True,
    )

    litellm_base_url: str = "http://localhost:4000"
    litellm_api_key: str = Field(
        default="sk-change-me",
        validation_alias=AliasChoices(
            "EVAL_SUT_LITELLM_API_KEY",
            "LITELLM_MASTER_KEY",
            "OPENAI_API_KEY",
        ),
    )
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "agentic_rag_eval_hybrid"
    embedding_model: str = "embed"
    rerank_model: str = "rerank"
    rerank_enabled: bool = False

    @property
    def openai_compatible_base_url(self) -> str:
        return f"{self.litellm_base_url.rstrip('/')}/v1"

    @property
    def proxy_api_key(self) -> str:
        return self.litellm_api_key

    def to_graph_deps(self, *, top_k: int | None = None) -> AgentGraphDeps:
        llm = LLMSettings(
            _env_file=None,
            litellm_base_url=self.litellm_base_url,
            openai_api_key=self.litellm_api_key,
        )
        return AgentGraphDeps(
            chat_client=OpenAIChatClient(llm),
            retrieval=create_async_retrieval_service(
                qdrant=QdrantSettings(
                    _env_file=None,
                    qdrant_url=self.qdrant_url,
                    qdrant_collection=self.qdrant_collection,
                ),
                llm=llm,
                embedding=EmbeddingSettings(
                    _env_file=None,
                    embedding_model=self.embedding_model,
                ),
                rerank=RerankSettings(
                    _env_file=None,
                    rerank_model=self.rerank_model,
                    rerank_enabled=self.rerank_enabled,
                ),
            ),
            qdrant_top_k=top_k if top_k is not None else 5,
        )


SUIT_REFUSAL_MARKERS: tuple[str, ...] = (
    "cannot find",
    "can't find",
    "could not find",
    "not available in the indexed",
    "not in the indexed excerpts",
    "no matching indexed",
    "provided context does not",
    "provided content does not",
    "context does not include",
    "context does not contain",
    "no relevant information",
    "no relevant excerpts",
    "not mentioned in the provided",
    "not mentioned in the context",
    "not specified in the",
    "the excerpts do not",
    "the documents do not",
    "no information in the indexed",
    "not present in the",
)


class SuitGenerationSettings(GenerationSettings):
    refusal_markers: tuple[str, ...] = SUIT_REFUSAL_MARKERS


class SuitSettings(EvalSettings):
    """Live suite: eval harness + host SUT + corpus-specific refusal markers."""

    sut: SutSettings = Field(default_factory=SutSettings)
    generation: SuitGenerationSettings = Field(default_factory=SuitGenerationSettings)


def eval_env_file() -> Path | None:
    path = EVAL_ROOT / ".env"
    return path if path.is_file() else None


def load_suit_settings() -> SuitSettings:
    file = eval_env_file()
    return SuitSettings(_env_file=file, sut=SutSettings(_env_file=file))
