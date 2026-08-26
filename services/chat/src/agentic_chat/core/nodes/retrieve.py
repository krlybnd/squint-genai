import logging

from agentic_shared.core.i18n import t
from agentic_shared.domains.retrieval.models import SearchMeta

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.nodes.protocols import GraphNode
from agentic_chat.core.state import (
    AgentState,
    AgentStateUpdate,
    chunk_states,
    locale_of,
    retrieve_result_update,
)

logger = logging.getLogger(__name__)


class RetrieveNode(GraphNode):
    def __init__(self, deps: AgentGraphDeps) -> None:
        self._deps = deps

    @property
    def node_id(self) -> AgentGraphNode:
        return AgentGraphNode.RETRIEVE

    async def __call__(self, state: AgentState) -> AgentStateUpdate:
        locale = locale_of(state)
        empty_chunks: list[dict[str, object]] = []

        needs_retrieval = state.get("needs_retrieval")
        if needs_retrieval is False:
            logger.debug("retrieve skipped")
            return retrieve_result_update(
                retrieved_chunks=empty_chunks,
                search_meta=SearchMeta.skipped_local(
                    state.get("rewrite_reason") or t("retrieve.skipped", locale),
                ),
            )

        search_query = (state.get("search_query") or state.get("query") or "").strip()
        if not search_query:
            logger.debug("retrieve skipped empty query")
            return retrieve_result_update(
                retrieved_chunks=empty_chunks,
                search_meta=SearchMeta.skipped_local(t("retrieve.empty_query", locale)),
            )

        tenant_id = state.get("tenant_id") or "default"
        parsed = await self._deps.retrieval.search_documents_with_meta(
            search_query,
            top_k=self._deps.qdrant_top_k,
            tenant_id=tenant_id,
        )
        chunks = chunk_states(parsed.chunks)
        meta = parsed.meta.model_copy(
            update={"search_query": search_query, "results_count": len(chunks)},
        )
        logger.info(
            "retrieved chunks=%d tenant_id=%s candidates=%d rerank=%s",
            len(chunks),
            tenant_id,
            parsed.meta.candidates_found,
            parsed.meta.rerank_applied,
        )
        return retrieve_result_update(retrieved_chunks=chunks, search_meta=meta)
