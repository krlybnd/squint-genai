from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from agentic_shared.core.settings.base import EnvSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from agentic_eval.core.deepeval.settings import DeepEvalSettings
from agentic_eval.core.goldendata.settings import GoldenSettings
from agentic_eval.modules.generation.settings import GenerationSettings
from agentic_eval.modules.retrieval.settings import RetrievalSettings

# tests/eval/src/agentic_eval/settings.py → parents[2]=tests/eval
EVAL_ROOT = Path(__file__).resolve().parents[2]


class EvalMode(StrEnum):
    mock = "mock"
    live = "live"


class EvalSettings(EnvSettings):
    """Eval harness. ``EVAL_`` prefix. Live stack URLs belong to suite ``SutSettings``."""

    model_config = SettingsConfigDict(env_prefix="EVAL_", extra="ignore", env_file=None)

    mode: EvalMode = EvalMode.mock
    tenant_id: str = "default"
    judge_model: str = "judge"
    max_concurrency: int = 20
    # One metric at a time. Faithfulness/Relevancy with async_mode still
    # fan out N claim checks; keep this at 1 under LiteLLM judge rpm: 30.
    judge_max_concurrency: int = 1
    judge_throttle_seconds: float = 2.0
    deepeval: DeepEvalSettings = Field(default_factory=DeepEvalSettings)
    golden: GoldenSettings = Field(default_factory=GoldenSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    generation: GenerationSettings = Field(default_factory=GenerationSettings)
