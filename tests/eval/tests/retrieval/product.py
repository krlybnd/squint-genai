"""Retrieval SUT: eval orchestration over ApiHttp search."""

from __future__ import annotations

from collections.abc import Sequence

from agentic_eval.core.clients.api import ApiHttp
from agentic_eval.core.settings import CoreSettings


class Product:
    def __init__(self, core: CoreSettings, *, top_k: int) -> None:
        headers = core.auth_headers()
        self._api = ApiHttp(core.api_url, headers=headers, max_connections=core.max_concurrency)
        self._top_k = top_k

    async def __aenter__(self) -> Product:
        await self._api.__aenter__()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self._api.__aexit__(*_exc)

    async def assert_catalog(self, expected: Sequence[str]) -> None:
        await self._api.assert_catalog(expected)

    async def search(self, question: str) -> list[str]:
        chunks = await self._api.search(question, top_k=self._top_k)
        return [chunk.source_file for chunk in chunks if chunk.source_file]
