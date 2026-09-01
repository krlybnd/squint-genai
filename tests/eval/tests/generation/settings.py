"""DeepEval generation gates. Compose ``CoreSettings`` for the OpenAI-compatible key."""

from __future__ import annotations

from dataclasses import dataclass

from agentic_shared.core.settings.module import ModuleSettings
from pydantic_settings import SettingsConfigDict

from agentic_eval.core.settings import EVAL_ROOT, CoreSettings, eval_env_file

REPORTS_DIR = EVAL_ROOT.parents[1] / "reports" / "eval"


class DeepEvalSettings(ModuleSettings):
    """Retry budget for Faithfulness / Answer Relevancy (gpt-4o 429s)."""

    model_config = SettingsConfigDict(
        env_prefix="EVAL_JUDGE_RETRY_",
        extra="ignore",
        env_file=None,
    )

    max_attempts: int = 10
    initial_seconds: float = 2.0
    cap_seconds: float = 60.0


class JudgeSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="EVAL_JUDGE_", extra="ignore", env_file=None)

    model: str = "judge"
    max_concurrency: int = 1
    throttle_seconds: float = 2.0


class GenerationGates(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="EVAL_GENERATION_", extra="ignore", env_file=None)

    correctness_threshold: float = 0.80
    faithfulness_threshold: float = 0.85
    answer_relevancy_threshold: float = 0.70
    refusal_markers: tuple[str, ...] = (
        "cannot find",
        "can't find",
        "could not find",
        "not available in the indexed",
        "this information is not available",
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


@dataclass(frozen=True)
class GenerationSettings:
    core: CoreSettings
    judge: JudgeSettings
    deepeval: DeepEvalSettings
    gates: GenerationGates

    @classmethod
    def load(cls) -> GenerationSettings:
        env = eval_env_file()
        return cls(
            core=CoreSettings(_env_file=env),
            judge=JudgeSettings(_env_file=env),
            deepeval=DeepEvalSettings(_env_file=env),
            gates=GenerationGates(_env_file=env),
        )
