"""API HTTP facade over the generated OpenAPI client."""

from __future__ import annotations

from collections.abc import Sequence

import httpx
from agentic_api_client import Client
from agentic_api_client.api.retrieval.get_source_citation_v1_retrieval_sources_chunk_id_get import (
    asyncio as get_source_citation,
)
from agentic_api_client.api.retrieval.list_indexed_documents_v1_retrieval_indexed_documents_get import (
    asyncio as list_indexed_documents,
)
from agentic_api_client.api.retrieval.search_documents_v1_retrieval_search_post import (
    asyncio as search_documents,
)
from agentic_api_client.errors import UnexpectedStatus
from agentic_api_client.models.chunk_out import ChunkOut
from agentic_api_client.models.citation_out import CitationOut
from agentic_api_client.models.indexed_document_out import IndexedDocumentOut
from agentic_api_client.models.search_request import SearchRequest
from agentic_api_client.models.search_response import SearchResponse
from agentic_api_client.types import UNSET

from agentic_eval.core.clients.catalog import catalog_blockers
from agentic_eval.core.clients.transport import client_kwargs

_HTTP = (httpx.HTTPError, UnexpectedStatus)


class ApiHttp:
    """Composes ``agentic_api_client.Client``."""

    def __init__(self, base_url: str, *, headers: dict[str, str], max_connections: int) -> None:
        self._client = Client(
            **client_kwargs(base_url, headers=headers, max_connections=max_connections)
        )

    async def __aenter__(self) -> ApiHttp:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self._client.__aexit__(*_exc)

    async def indexed_documents(self) -> list[IndexedDocumentOut]:
        try:
            raw = await list_indexed_documents(client=self._client)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"api unreachable: {exc}") from exc
        if not isinstance(raw, list):
            raise RuntimeError("api catalog returned a non-list payload")
        return [item for item in raw if isinstance(item, IndexedDocumentOut)]

    async def assert_catalog(self, expected: Sequence[str]) -> None:
        try:
            items = await self.indexed_documents()
        except UnexpectedStatus as exc:
            if exc.status_code in {401, 403}:
                raise RuntimeError(
                    f"api catalog HTTP {exc.status_code}. "
                    "Set EVAL_SUT_INTERNAL_SERVICE_KEY (or API_KEY) in tests/eval/.env "
                    "to match the stack when AUTH_MODE is jwt or api_key."
                ) from exc
            raise RuntimeError(f"api catalog HTTP {exc.status_code}") from exc
        blocked = catalog_blockers(
            [(item.source_file, item.doc_id) for item in items if item.source_file],
            expected,
        )
        if blocked:
            raise RuntimeError(blocked)

    async def search(self, query: str, *, top_k: int | None = None) -> list[ChunkOut]:
        try:
            raw = await search_documents(
                client=self._client, body=SearchRequest(query=query, top_k=top_k)
            )
        except httpx.HTTPError as exc:
            raise RuntimeError(f"api search unreachable: {exc}") from exc
        if not isinstance(raw, SearchResponse):
            raise RuntimeError(f"api search failed: {raw}")
        return list(raw.chunks)

    async def citation(self, chunk_id: str) -> CitationOut | None:
        try:
            raw = await get_source_citation(chunk_id, client=self._client)
        except _HTTP:
            return None
        return raw if isinstance(raw, CitationOut) else None

    async def citation_text(self, chunk_id: str) -> str:
        found = await self.citation(chunk_id)
        if found is None:
            return ""
        raw = found.text if found.text not in (None, UNSET) else found.excerpt
        return raw if isinstance(raw, str) else ""
