"""Documents module — upload and indexing orchestration tunables."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class DocumentsModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="API_DOCUMENTS_")

    max_upload_size_mb: int = Field(
        default=50,
        description="Maximum allowed PDF upload size in megabytes.",
    )


get_module_settings = module_settings_loader(DocumentsModuleSettings)
