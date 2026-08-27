"""DeepEval runtime tunables (retry policy for the judge LLM)."""

from __future__ import annotations

from agentic_shared.core.settings.module import ModuleSettings
from deepeval.config.settings import get_settings
from pydantic_settings import SettingsConfigDict


class DeepEvalSettings(ModuleSettings):
    """Retry budget for Faithfulness / Answer Relevancy (gpt-4o 429s).

    Applied onto DeepEval's live ``Settings`` singleton — not ``os.environ``.
    """

    model_config = SettingsConfigDict(
        env_prefix="EVAL_JUDGE_RETRY_",
        extra="ignore",
        env_file=None,
    )

    max_attempts: int = 10
    initial_seconds: float = 2.0
    cap_seconds: float = 60.0

    def apply(self) -> None:
        live = get_settings()
        live.DEEPEVAL_RETRY_MAX_ATTEMPTS = self.max_attempts
        live.DEEPEVAL_RETRY_INITIAL_SECONDS = self.initial_seconds
        live.DEEPEVAL_RETRY_CAP_SECONDS = self.cap_seconds
