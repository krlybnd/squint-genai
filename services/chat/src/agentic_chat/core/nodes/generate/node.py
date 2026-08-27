import logging
from dataclasses import dataclass

from agentic_shared.core.i18n import t
from agentic_shared.core.security.guard import redact_for_provider
from agentic_shared.domains.retrieval.models import ChunkCitation, RetrievedChunk
from agentic_shared.integrations.llm.messages import llm_system_user
from agentic_shared.integrations.llm.settings import LLMSettings

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.nodes.generate.settings import get_module_settings
from agentic_chat.core.nodes.protocols import LlmCallNode
from agentic_chat.core.state import (
    AgentState,
    AgentStateUpdate,
    generate_answer_update,
    locale_of,
)
from agentic_chat.core.state.models import RetrievedChunkState

logger = logging.getLogger(__name__)


def _chunk_line(chunk: RetrievedChunk) -> str:
    text = redact_for_provider(chunk.text).text
    page = chunk.page if chunk.page is not None else "?"
    return f"[{chunk.source_file or 'doc'} p.{page}] {text}"


def _chunks_from_state(state: AgentState) -> list[RetrievedChunk]:
    raw_chunks = state.get("retrieved_chunks", [])
    return [
        RetrievedChunk.model_validate(RetrievedChunkState.model_validate(c).model_dump())
        for c in raw_chunks
        if isinstance(c, dict)
    ]


@dataclass(frozen=True)
class _GenerateContext:
    locale: str
    query: str
    citations: list[ChunkCitation]


class GenerateNode(LlmCallNode[_GenerateContext]):
    def __init__(self, deps: AgentGraphDeps) -> None:
        super().__init__(deps)

    @property
    def node_id(self) -> AgentGraphNode:
        return AgentGraphNode.GENERATE

    async def prepare(self, state: AgentState) -> tuple[AgentStateUpdate | None, _GenerateContext]:
        locale = locale_of(state)
        query = state.get("safe_query") or state.get("query", "")
        chunks = _chunks_from_state(state)
        context = "\n\n".join(_chunk_line(c) for c in chunks)
        citations = [ChunkCitation.from_chunk(c) for c in chunks] if context.strip() else []
        return None, _GenerateContext(locale=locale, query=query, citations=citations)

    async def build_messages(
        self, state: AgentState, ctx: _GenerateContext
    ) -> list[dict[str, str]]:
        module = get_module_settings()
        chunks = _chunks_from_state(state)
        context = "\n\n".join(_chunk_line(c) for c in chunks)
        if not context.strip():
            return llm_system_user(module.no_context_system_prompt, ctx.query)
        return llm_system_user(
            module.rag_system_prompt,
            f"Context:\n{context}\n\nQuestion: {ctx.query}",
        )

    def on_success(
        self, state: AgentState, content: str, ctx: _GenerateContext
    ) -> AgentStateUpdate:
        logger.debug("generated answer citations=%d chars=%d", len(ctx.citations), len(content))
        return generate_answer_update(answer=content, citations=ctx.citations)

    def on_error(self, state: AgentState, ctx: _GenerateContext) -> AgentStateUpdate:
        logger.warning("generate fallback answer citations=%d", len(ctx.citations))
        return generate_answer_update(
            answer=t("generate.error", ctx.locale),
            citations=ctx.citations,
        )

    def llm_temperature(self) -> float:
        return get_module_settings().llm_temperature

    def llm_model(self) -> str | None:
        return LLMSettings().litellm_model
