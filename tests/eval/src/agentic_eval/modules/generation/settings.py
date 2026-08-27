from agentic_shared.core.settings.module import ModuleSettings
from pydantic_settings import SettingsConfigDict

DEFAULT_REFUSAL_MARKERS: tuple[str, ...] = (
    "cannot find",
    "can't find",
    "could not find",
    "no relevant information",
)


class GenerationSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="EVAL_GENERATION_", extra="ignore", env_file=None)

    faithfulness_threshold: float = 0.70
    answer_relevancy_threshold: float = 0.55
    refusal_markers: tuple[str, ...] = DEFAULT_REFUSAL_MARKERS
