"""PDF semantic chunking pipeline tunables."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class PdfIndexingModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="INDEXING_PDF_")

    semantic_buffer_size: int = Field(
        default=1,
        description="LlamaIndex SemanticSplitter buffer_size (sentences around breakpoint).",
    )
    semantic_breakpoint_percentile_threshold: int = Field(
        default=95,
        description="Percentile threshold for semantic breakpoints (higher → fewer chunks).",
    )


get_module_settings = module_settings_loader(PdfIndexingModuleSettings)
