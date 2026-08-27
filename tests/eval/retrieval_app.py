"""Retrieval-only entry point for Tier-1 eval (hybrid search + rerank)."""

from __future__ import annotations

from agentic_chat.core.deps import agent_graph_deps_from_settings

from bootstrap_env import configure_llm_env_for_eval

TENANT_ID = "default"


async def retrieve_ranked_source_files(
    question: str,
    *,
    top_k: int | None = None,
) -> list[str]:
    configure_llm_env_for_eval()
    deps = agent_graph_deps_from_settings()
    final_k = top_k if top_k is not None else deps.qdrant_top_k
    result = await deps.retrieval.search_documents_with_meta(
        question,
        top_k=final_k,
        tenant_id=TENANT_ID,
    )
    return [chunk.source_file for chunk in result.chunks if chunk.source_file]
