from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from agentic_shared.domains.annotations.models import ChunkComment
from agentic_shared.domains.retrieval.enums import FusionStrategy, SearchType
from agentic_shared.infrastructure.vector.types import VectorPayload


class ChunkPointPayload(VectorPayload):
    """Indexed chunk point stored in Qdrant."""

    comments: list[ChunkComment] = Field(default_factory=list)


class RetrievedChunk(BaseModel):
    """Chunk returned from Qdrant hybrid search or scroll APIs."""

    model_config = ConfigDict(extra="allow")

    chunk_id: str = ""
    doc_id: str | None = None
    source_file: str = ""
    page: int | str | None = None
    text: str = ""
    score: float | None = None
    comments: list[ChunkComment] | None = None


class ChunkCitation(BaseModel):
    chunk_id: str
    doc_id: str = ""
    source_file: str = ""
    page: int | str | None = None
    excerpt: str = ""

    @classmethod
    def from_chunk(cls, chunk: RetrievedChunk, *, excerpt_len: int = 200) -> Self:
        return cls(
            chunk_id=chunk.chunk_id,
            doc_id=str(chunk.doc_id or ""),
            source_file=chunk.source_file,
            page=chunk.page,
            excerpt=chunk.text[:excerpt_len],
        )


class ChunkPreview(BaseModel):
    chunk_id: str = ""
    source_file: str | None = None
    page: int | str | None = None
    score: float | None = None
    excerpt: str = ""
    rank: int = 0
    selected: bool = False

    @classmethod
    def from_chunk(
        cls,
        chunk: RetrievedChunk,
        *,
        rank: int,
        selected: bool = False,
        excerpt_len: int = 280,
    ) -> Self:
        return cls(
            chunk_id=chunk.chunk_id,
            source_file=chunk.source_file or None,
            page=chunk.page,
            score=chunk.score,
            excerpt=chunk.text[:excerpt_len],
            rank=rank,
            selected=selected,
        )


class SearchMeta(BaseModel):
    """Metadata for hybrid search, chat skip paths, and eval/debug SSE."""

    model_config = ConfigDict(extra="forbid")

    query: str = ""
    search_type: SearchType = SearchType.HYBRID
    dense: bool = True
    sparse: bool = True
    fusion: FusionStrategy = FusionStrategy.RRF
    dense_model: str = ""
    sparse_model: str = ""
    candidate_top_k: int = 0
    final_top_k: int = 0
    candidates_found: int = 0
    results_count: int = 0
    rerank_enabled: bool = False
    rerank_model: str = ""
    rerank_applied: bool = False
    rerank_skip_reason: str | None = None
    rerank_error: str | None = None
    skipped: bool = False
    reason: str = ""
    search_query: str = ""
    error: str | None = None
    rrf_candidates: list[ChunkPreview] = Field(default_factory=list)
    final_chunks: list[ChunkPreview] = Field(default_factory=list)

    @classmethod
    def skipped_local(cls, reason: str, *, search_query: str = "") -> Self:
        return cls(skipped=True, reason=reason, search_query=search_query)

    @classmethod
    def hybrid_start(
        cls,
        *,
        query: str,
        dense_model: str,
        sparse_model: str,
        candidate_top_k: int,
        final_top_k: int,
        rerank_enabled: bool,
        rerank_model: str,
    ) -> Self:
        return cls(
            query=query,
            dense_model=dense_model,
            sparse_model=sparse_model,
            candidate_top_k=candidate_top_k,
            final_top_k=final_top_k,
            rerank_enabled=rerank_enabled,
            rerank_model=rerank_model,
            rerank_skip_reason=(
                None
                if rerank_enabled
                else "disabled (requires COHERE_API_KEY via LiteLLM; OpenAI has no rerank API)"
            ),
        )

    def with_error(self, message: str) -> Self:
        return self.model_copy(update={"error": message})

    def with_candidate_count(self, count: int) -> Self:
        return self.model_copy(update={"candidates_found": count, "results_count": count})


class SearchDocumentsResult(BaseModel):
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    meta: SearchMeta = Field(default_factory=SearchMeta)


class SourceCitation(BaseModel):
    chunk_id: str
    page: str | int | None = None
    section: str | None = None
    source_file: str | None = None
    doc_id: str | None = None
    text: str = ""
    excerpt: str = ""
    error: str | None = None


class IndexedDocumentEntry(BaseModel):
    doc_id: str
    source_file: str = ""
    chunk_count: int = 0
