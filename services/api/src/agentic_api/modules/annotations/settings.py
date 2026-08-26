"""Annotations moderation tunables."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic_settings import SettingsConfigDict


class AnnotationsModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="API_ANNOTATIONS_")

    comment_min_length: int = 2
    comment_max_length: int = 2000
    moderation_temperature: float = 0.0


get_module_settings = module_settings_loader(AnnotationsModuleSettings)
