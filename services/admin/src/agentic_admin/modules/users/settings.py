"""Admin users module settings (extend when user-specific config is needed)."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic_settings import SettingsConfigDict


class UsersModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="ADMIN_USERS_")


get_module_settings = module_settings_loader(UsersModuleSettings)
