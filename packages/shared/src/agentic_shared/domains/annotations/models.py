from pydantic import BaseModel, ConfigDict, Field


class ChunkComment(BaseModel):
    """Comment embedded in a chunk's Qdrant payload (`comments` list)."""

    model_config = ConfigDict(extra="ignore")

    comment_id: str = Field(min_length=1)
    selected_text: str = ""
    comment_text: str = Field(min_length=1)
    user_id: str | None = None
    created_at: str = ""
