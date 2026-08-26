"""Chat module tunables (streaming, session titles, retrieval overrides)."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic_settings import SettingsConfigDict


class ChatModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="CHAT_")

    session_title_temperature: float = 0.3
    session_title_max_chars: int = 120
    user_message_preview_chars: int = 500
    qdrant_top_k: int | None = None


get_module_settings = module_settings_loader(ChatModuleSettings)
