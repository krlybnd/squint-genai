from __future__ import annotations

import uuid
from typing import Self

from pydantic import BaseModel, ConfigDict, Field


class IndexDocumentTaskResult(BaseModel):
    """Outcome of a successful ``indexing.index_document`` Celery run."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(min_length=1)
    chunk_count: int = Field(ge=0)

    @classmethod
    def from_run(cls, *, document_id: uuid.UUID, chunk_count: int) -> Self:
        return cls(document_id=str(document_id), chunk_count=chunk_count)

    def to_celery_result(self) -> dict[str, str | int]:
        """JSON-serializable payload for Celery result backend."""
        return self.model_dump(mode="json")
