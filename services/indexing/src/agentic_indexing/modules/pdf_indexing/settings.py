"""PDF semantic chunking pipeline tunables."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic_settings import SettingsConfigDict


class PdfIndexingModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="INDEXING_PDF_")

    semantic_buffer_size: int = 1
    semantic_breakpoint_percentile_threshold: int = 95


get_module_settings = module_settings_loader(PdfIndexingModuleSettings)
