"""Retrieval IR gates. Compose ``CoreSettings`` for LiteLLM key and api/chat URLs."""

from __future__ import annotations

from dataclasses import dataclass

from agentic_shared.core.settings.module import ModuleSettings
from pydantic import BaseModel, ConfigDict
from pydantic_settings import SettingsConfigDict

from agentic_eval.core.settings import CoreSettings, eval_env_file


class RetrievalMinimums(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_recall_at_k: float = 0.90
    chunk_precision_at_k: float = 0.85
    hit_rate_at_k: float = 0.90
    mrr: float = 0.80
    ndcg_at_k: float = 0.80


class RetrievalGates(ModuleSettings):
    model_config = SettingsConfigDict(
        env_prefix="EVAL_RETRIEVAL_",
        extra="ignore",
        env_file=None,
        env_nested_delimiter="_",
        nested_model_default_partial_update=True,
    )

    k: int = 5
    minimums: RetrievalMinimums = RetrievalMinimums()


@dataclass(frozen=True)
class RetrievalSettings:
    core: CoreSettings
    gates: RetrievalGates

    @classmethod
    def load(cls) -> RetrievalSettings:
        env = eval_env_file()
        return cls(
            core=CoreSettings(_env_file=env),
            gates=RetrievalGates(_env_file=env),
        )

    @property
    def k(self) -> int:
        return self.gates.k

    @property
    def minimums(self) -> RetrievalMinimums:
        return self.gates.minimums
