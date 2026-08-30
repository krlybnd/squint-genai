"""Rewrite-router node tunables."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class RewriteNodeSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="CHAT_REWRITE_")

    llm_temperature: float = Field(
        default=0.1,
        description="LLM temperature for query rewrite / routing decisions.",
    )
    indexed_catalog_limit: int = Field(
        default=25,
        description="Max indexed document catalog entries shown to the rewrite prompt.",
    )


get_module_settings = module_settings_loader(RewriteNodeSettings)
