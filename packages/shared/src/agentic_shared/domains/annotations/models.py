from pydantic import ConfigDict, Field

from agentic_shared.infrastructure.vector.core.types import VectorPayload


class ChunkComment(VectorPayload):
    """Comment embedded in a chunk's Qdrant payload (`comments` list)."""

    model_config = ConfigDict(extra="ignore")

    comment_id: str = Field(min_length=1)
    selected_text: str = ""
    comment_text: str = Field(min_length=1)
    user_id: str | None = None
    created_at: str = ""


class CommentPointPayload(VectorPayload):
    """Standalone comment vector point stored in Qdrant."""

    comment_id: str = Field(min_length=1)
    parent_chunk_id: str = Field(min_length=1)
    selected_text: str = ""
    comment_text: str = ""
    user_id: str | None = None
    created_at: str = ""
