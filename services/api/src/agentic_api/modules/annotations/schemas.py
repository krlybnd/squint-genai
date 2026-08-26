from datetime import datetime
from typing import Self

from agentic_shared.domains.annotations.models import ChunkComment
from pydantic import BaseModel, Field


class CreateChunkCommentRequest(BaseModel):
    selected_text: str = Field(min_length=1, max_length=4000)
    comment_text: str = Field(min_length=2, max_length=2000)


class ChunkCommentOut(BaseModel):
    comment_id: str
    chunk_id: str
    selected_text: str
    comment_text: str
    user_id: str | None = None
    created_at: datetime | str

    @classmethod
    def from_stored(cls, chunk_id: str, comment: ChunkComment) -> Self:
        return cls(
            comment_id=comment.comment_id,
            chunk_id=chunk_id,
            selected_text=comment.selected_text,
            comment_text=comment.comment_text,
            user_id=comment.user_id,
            created_at=comment.created_at,
        )
