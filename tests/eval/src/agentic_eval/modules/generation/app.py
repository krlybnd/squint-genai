"""Chat-graph SUT for Tier 2 generation eval."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import Any

from agentic_chat.core.graph import build_graph
from agentic_chat.core.state import AgentGraphInput, graph_config, graph_message
from agentic_shared.domains.chat.roles import ChatMessageRole
from langgraph.checkpoint.memory import MemorySaver

from agentic_eval.core.protocols import HostStack
from agentic_eval.modules.generation.types import GenerationResult

THREAD_ID = "eval"


def _contexts_from_result(result: dict[str, Any]) -> list[str]:
    chunks = result.get("retrieved_chunks") or []
    return [
        chunk["text"]
        for chunk in chunks
        if isinstance(chunk, dict) and isinstance(chunk.get("text"), str)
    ]


def build_eval_graph(stack: HostStack, *, top_k: int) -> Any:
    return build_graph(MemorySaver(), deps=stack.to_graph_deps(top_k=top_k))


async def answer_question(
    question: str,
    *,
    tenant_id: str,
    graph: Any,
) -> GenerationResult:
    thread_id = f"{THREAD_ID}-{hash(question) & 0xFFFFFFFF:x}"
    state = AgentGraphInput(
        messages=[graph_message(ChatMessageRole.USER, question)],
        thread_id=thread_id,
        tenant_id=tenant_id,
    ).as_state()
    result = await graph.ainvoke(state, graph_config(thread_id=thread_id))
    raw_answer = result.get("answer") or ""
    answer = raw_answer if isinstance(raw_answer, str) else ""
    return GenerationResult(answer=answer, contexts=_contexts_from_result(result))


async def answer_questions(
    questions: Sequence[str],
    *,
    tenant_id: str,
    graph: Any,
    max_concurrent: int,
    on_done: Callable[[], None] | None = None,
) -> list[GenerationResult]:
    """Run the graph on every question, capped by ``max_concurrent``."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def one(question: str) -> GenerationResult:
        async with semaphore:
            result = await answer_question(question, tenant_id=tenant_id, graph=graph)
        if on_done is not None:
            on_done()
        return result

    return list(await asyncio.gather(*[one(question) for question in questions]))


def run_question(question: str, *, tenant_id: str, graph: Any) -> GenerationResult:
    return asyncio.run(answer_question(question, tenant_id=tenant_id, graph=graph))
