"""Retrieval API module defaults."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic_settings import SettingsConfigDict


class RetrievalModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="API_RETRIEVAL_")

    default_top_k: int | None = None


get_module_settings = module_settings_loader(RetrievalModuleSettings)
