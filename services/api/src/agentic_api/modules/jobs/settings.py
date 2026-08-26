"""Jobs module — Celery task names and broker-facing config."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic_settings import SettingsConfigDict


class JobsModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="API_JOBS_")

    celery_app_name: str = "agentic_indexing"
    index_document_task_name: str = "indexing.index_document"


get_module_settings = module_settings_loader(JobsModuleSettings)
