"""Generation SUT: eval orchestration over ChatHttp + ApiHttp."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from sys import stdout

from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeElapsedColumn

from agentic_eval.core.clients.api import ApiHttp
from agentic_eval.core.clients.chat import ChatHttp
from agentic_eval.core.clients.sse import answer_and_citations, strip_vault_marks
from agentic_eval.core.settings import CoreSettings


class Product:
    def __init__(self, core: CoreSettings) -> None:
        headers = core.auth_headers()
        self._chat = ChatHttp(core.chat_url, headers=headers, max_connections=core.max_concurrency)
        self._api = ApiHttp(core.api_url, headers=headers, max_connections=core.max_concurrency)
        self._max_concurrent = core.max_concurrency

    async def __aenter__(self) -> Product:
        await self._chat.__aenter__()
        await self._api.__aenter__()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self._api.__aexit__(*_exc)
        await self._chat.__aexit__(*_exc)

    async def assert_ready(self) -> None:
        await self._chat.ready()

    async def assert_catalog(self, expected: Sequence[str]) -> None:
        await self._api.assert_catalog(expected)

    async def ask(self, question: str) -> tuple[str, list[str]]:
        session_id = await self._chat.create_session(title="eval")
        try:
            events = await self._chat.stream(session_id, question)
            answer, citations = answer_and_citations(events)
            return answer, await self._contexts(citations)
        finally:
            await self._chat.delete_session(session_id)

    async def ask_many(
        self, questions: Sequence[str], *, description: str
    ) -> list[tuple[str, list[str]]]:
        if not questions:
            return []
        semaphore = asyncio.Semaphore(self._max_concurrent)
        with Progress(
            TextColumn("{task.description}"),
            BarColumn(bar_width=60),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=Console(file=stdout),
        ) as progress:
            task_id = progress.add_task(description, total=len(questions))

            async def one(question: str) -> tuple[str, list[str]]:
                async with semaphore:
                    result = await self.ask(question)
                progress.advance(task_id)
                return result

            return list(await asyncio.gather(*[one(q) for q in questions]))

    async def _contexts(self, citations: Sequence[object]) -> list[str]:
        texts: list[str] = []
        for item in citations:
            if not isinstance(item, dict):
                continue
            chunk_id = item.get("chunk_id")
            excerpt = item.get("text") or item.get("excerpt") or ""
            fallback = strip_vault_marks(excerpt) if isinstance(excerpt, str) else ""
            if isinstance(chunk_id, str) and chunk_id:
                full = strip_vault_marks(await self._api.citation_text(chunk_id))
                texts.append(full or fallback)
            elif fallback:
                texts.append(fallback)
        return [text for text in texts if text]
