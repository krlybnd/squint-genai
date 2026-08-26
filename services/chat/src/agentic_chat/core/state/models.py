from __future__ import annotations

from typing import Any, Self

from agentic_shared.domains.retrieval.models import ChunkCitation, RetrievedChunk, SearchMeta
from pydantic import BaseModel, ConfigDict


class CitationState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunk_id: str = ""
    doc_id: str = ""
    source_file: str = ""
    page: int | str | None = None
    excerpt: str = ""

    @classmethod
    def from_citation(cls, citation: ChunkCitation) -> Self:
        return cls.model_validate(citation.model_dump())

    def to_state(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class RetrievedChunkState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunk_id: str = ""
    doc_id: str | None = None
    source_file: str = ""
    page: int | str | None = None
    text: str = ""
    score: float | None = None

    @classmethod
    def from_chunk(cls, chunk: RetrievedChunk) -> Self:
        return cls.model_validate(chunk.model_dump())

    def to_state(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class SearchMetaState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    query: str = ""
    search_query: str = ""
    search_type: str = ""
    fusion: str = ""
    dense: bool = False
    sparse: bool = False
    skipped: bool = False
    reason: str = ""
    error: str | None = None
    results_count: int = 0
    candidates_found: int = 0

    @classmethod
    def from_meta(cls, meta: SearchMeta) -> Self:
        return cls.model_validate(meta.model_dump(mode="json"))

    def to_state(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


def citation_states(citations: list[ChunkCitation]) -> list[dict[str, Any]]:
    return [CitationState.from_citation(c).to_state() for c in citations]


def chunk_states(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    return [RetrievedChunkState.from_chunk(c).to_state() for c in chunks]


def search_meta_state(meta: SearchMeta) -> dict[str, Any]:
    return SearchMetaState.from_meta(meta).to_state()
