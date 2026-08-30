"""Chat module tunables (streaming, session titles, retrieval overrides)."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class ChatModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="CHAT_")

    session_title_temperature: float = Field(
        default=0.3,
        description="LLM temperature when auto-generating a chat session title.",
    )
    session_title_max_chars: int = Field(
        default=120,
        description="Hard cap on generated session title length.",
    )
    user_message_preview_chars: int = Field(
        default=500,
        description="Chars of the user message kept for title/preview prompts.",
    )
    qdrant_top_k: int | None = Field(
        default=None,
        description=("Optional override for retrieval top_k in chat. None → QdrantSettings.top_k."),
    )


get_module_settings = module_settings_loader(ChatModuleSettings)
