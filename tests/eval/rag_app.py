"""Entry point under evaluation: the real chat graph (retrieve + generate)."""

from __future__ import annotations

from agentic_chat.core.graph import build_graph
from agentic_chat.core.state import AgentGraphInput, graph_config, graph_message
from agentic_shared.domains.chat.roles import ChatMessageRole
from langgraph.checkpoint.memory import MemorySaver

from bootstrap_env import configure_llm_env_for_eval

TENANT_ID = "default"
THREAD_ID = "eval"


async def answer_question(question: str) -> tuple[str, list[str]]:
    """Return the generated answer plus the chunk texts it was grounded on."""
    configure_llm_env_for_eval()
    graph = build_graph(MemorySaver())
    state = AgentGraphInput(
        messages=[graph_message(ChatMessageRole.USER, question)],
        thread_id=THREAD_ID,
        tenant_id=TENANT_ID,
    ).as_state()

    result = await graph.ainvoke(state, graph_config(thread_id=THREAD_ID))

    chunks = result.get("retrieved_chunks") or []
    contexts = [c["text"] for c in chunks if isinstance(c, dict) and c.get("text")]
    return result.get("answer") or "", contexts
