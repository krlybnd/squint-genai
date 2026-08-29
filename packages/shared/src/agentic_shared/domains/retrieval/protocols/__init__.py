from typing import Protocol, runtime_checkable

from agentic_shared.domains.retrieval.models import (
    IndexedDocumentEntry,
    RetrievedChunk,
    SearchDocumentsResult,
    SourceCitation,
)


@runtime_checkable
class AsyncRetrievalReader(Protocol):
    async def search_documents(
        self, query: str, top_k: int | None = None, *, tenant_id: str
    ) -> list[RetrievedChunk]: ...

    async def search_documents_with_meta(
        self, query: str, top_k: int | None = None, *, tenant_id: str
    ) -> SearchDocumentsResult: ...

    async def get_source_citation(self, chunk_id: str, *, tenant_id: str) -> SourceCitation: ...

    async def list_indexed_documents(self, *, tenant_id: str) -> list[IndexedDocumentEntry]: ...

    async def list_document_chunks(
        self, doc_id: str, *, tenant_id: str, limit: int = 500
    ) -> list[RetrievedChunk]: ...

    async def list_source_file_chunks(
        self, source_file: str, *, tenant_id: str, limit: int = 500
    ) -> list[RetrievedChunk]: ...
