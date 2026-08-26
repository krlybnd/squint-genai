from uuid import UUID

from pydantic import BaseModel, Field


class JobOut(BaseModel):
    id: UUID
    document_id: UUID | None
    celery_task_id: str | None
    status: str
    error_message: str | None
    created_at: str
    completed_at: str | None

    model_config = {"from_attributes": True}


class IndexAllResponse(BaseModel):
    job_ids: list[UUID] = Field(default_factory=list)
    message: str
