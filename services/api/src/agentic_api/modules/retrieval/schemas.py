from agentic_shared.domains.annotations.models import ChunkComment
from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=50)


class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    text: str
    score: float | None = None
    doc_id: str | None = None
    source_file: str | None = None
    page: int | str | None = None
    comments: list[ChunkComment] | None = None


class SearchResponse(BaseModel):
    chunks: list[ChunkOut]


class CitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    page: int | str | None = None
    section: str | None = None
    source_file: str | None = None
    doc_id: str | None = None
    text: str | None = None
    excerpt: str | None = None
    error: str | None = None


class DocumentChunksResponse(BaseModel):
    doc_id: str
    source_file: str | None = None
    chunks: list[ChunkOut]


class IndexedDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doc_id: str
    source_file: str
    chunk_count: int
