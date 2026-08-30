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
    pii_tokenization_enabled: bool = Field(
        default=False,
        description="Tokenize PII before chunking/embed (requires Presidio analyzer).",
    )
    pii_language: str = Field(
        default="en",
        description="Presidio analyzer language for index-time PII detection.",
    )


get_module_settings = module_settings_loader(PdfIndexingModuleSettings)
