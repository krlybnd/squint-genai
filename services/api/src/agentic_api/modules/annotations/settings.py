"""Annotations moderation tunables."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class AnnotationsModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="API_ANNOTATIONS_")

    comment_min_length: int = Field(
        default=2,
        description="Minimum accepted annotation comment length (characters).",
    )
    comment_max_length: int = Field(
        default=2000,
        description="Maximum accepted annotation comment length (characters).",
    )
    moderation_temperature: float = Field(
        default=0.0,
        description="LLM temperature for comment moderation / classification.",
    )


get_module_settings = module_settings_loader(AnnotationsModuleSettings)
