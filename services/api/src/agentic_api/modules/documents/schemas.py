from datetime import datetime
from uuid import UUID

from agentic_shared.domains.documents.enums import IndexStatus
from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: UUID
    filename: str
    minio_key: str
    page_count: int | None
    indexed_at: datetime | None
    index_status: IndexStatus = IndexStatus.PENDING
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentOut]
    total: int


class PresignUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=512)


class PresignUploadResponse(BaseModel):
    document: DocumentOut
    upload_url: str = Field(description="PUT target URL (via API proxy to object storage)")
    expires_in: int = Field(description="URL validity in seconds")
    content_type: str = "application/pdf"


class CompleteUploadResponse(BaseModel):
    document: DocumentOut
    job_id: UUID = Field(description="Celery indexing job id")


class ReindexDocumentResponse(BaseModel):
    document: DocumentOut
    job_id: UUID = Field(description="Celery reindexing job id")
