"""Admin tenants module settings (extend when tenant-specific config is needed)."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic_settings import SettingsConfigDict


class TenantsModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="ADMIN_TENANTS_")


get_module_settings = module_settings_loader(TenantsModuleSettings)
