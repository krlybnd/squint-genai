"""Rewrite-router node tunables."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic_settings import SettingsConfigDict


class RewriteNodeSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="CHAT_REWRITE_")

    llm_temperature: float = 0.1
    indexed_catalog_limit: int = 25


get_module_settings = module_settings_loader(RewriteNodeSettings)
