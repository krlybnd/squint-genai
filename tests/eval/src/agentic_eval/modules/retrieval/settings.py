from agentic_shared.core.settings.module import ModuleSettings
from pydantic_settings import SettingsConfigDict

from agentic_eval.modules.retrieval.metrics import DEFAULT_RETRIEVAL_MINIMUMS, RetrievalScores


class RetrievalSettings(ModuleSettings):
    model_config = SettingsConfigDict(
        env_prefix="EVAL_RETRIEVAL_",
        extra="ignore",
        env_file=None,
        env_nested_delimiter="_",
        nested_model_default_partial_update=True,
    )

    k: int = 5
    minimums: RetrievalScores = DEFAULT_RETRIEVAL_MINIMUMS
