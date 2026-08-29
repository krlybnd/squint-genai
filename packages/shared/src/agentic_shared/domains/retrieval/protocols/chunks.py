from typing import Any, Protocol, runtime_checkable

from qdrant_client.http.models import SparseVector

from agentic_shared.domains.retrieval.models import (
    ChunkPointPayload,
    IndexedDocumentEntry,
    RetrievedChunk,
)
from agentic_shared.infrastructure.vector.protocols import (
    VectorReadRepository,
    VectorWriteRepository,
)
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings


@runtime_checkable
class ChunkReadRepository(VectorReadRepository[ChunkPointPayload], Protocol):
    @property
    def default_top_k(self) -> int: ...

    @property
    def candidate_top_k(self) -> int: ...

    @property
    def sparse_model(self) -> str: ...

    def hybrid_search(
        self,
        *,
        tenant_id: str,
        dense_vector: list[float],
        sparse_vector: SparseVector,
        limit: int,
    ) -> list[RetrievedChunk]: ...

    def scroll_document_catalog(self, *, tenant_id: str) -> list[IndexedDocumentEntry]: ...

    def scroll_document_chunks(
        self,
        doc_id: str,
        *,
        tenant_id: str,
        limit: int = 100,
        offset: str | None = None,
    ) -> tuple[list[RetrievedChunk], str | None]: ...

    def scroll_source_file_chunks(
        self,
        source_file: str,
        *,
        tenant_id: str,
        limit: int = 100,
        offset: str | None = None,
    ) -> tuple[list[RetrievedChunk], str | None]: ...


@runtime_checkable
class ChunkWriteRepository(VectorWriteRepository[ChunkPointPayload], Protocol):
    def ensure_collection(self, *, vector_dim: int = 1536) -> None: ...

    def index_nodes(
        self,
        nodes: list[Any],
        *,
        llm: LLMSettings,
        embedding: EmbeddingSettings,
    ) -> int: ...

    def delete_by_doc_id(self, doc_id: str, *, tenant_id: str) -> None: ...
