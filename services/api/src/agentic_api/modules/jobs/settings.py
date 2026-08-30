"""Jobs module — Celery task names and broker-facing config."""

from agentic_shared.core.settings.module import ModuleSettings, module_settings_loader
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class JobsModuleSettings(ModuleSettings):
    model_config = SettingsConfigDict(env_prefix="API_JOBS_")

    celery_app_name: str = Field(
        default="agentic_indexing",
        description="Celery application name used when enqueueing index tasks.",
    )
    index_document_task_name: str = Field(
        default="indexing.index_document",
        description="Fully-qualified Celery task name for document indexing.",
    )


get_module_settings = module_settings_loader(JobsModuleSettings)
