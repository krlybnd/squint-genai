from collections.abc import AsyncIterator

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.state import AgentStateUpdate
from agentic_chat.modules.chat.streaming.sse_events import sse_reasoning
from agentic_chat.modules.chat.streaming.sse_reasoning_handlers import NODE_DONE_HANDLERS
from agentic_chat.modules.chat.streaming.sse_transitions import active_events_after


async def events_for_node(
    node: str,
    output: AgentStateUpdate,
    checkpoint_id: str | None,
    locale: str,
) -> AsyncIterator[str]:
    graph_node = AgentGraphNode.from_stream_name(node)
    if graph_node is None:
        return

    handler = NODE_DONE_HANDLERS.get(graph_node)
    if handler is None:
        return

    yield sse_reasoning(handler(output, locale).with_checkpoint(checkpoint_id))
    for event in active_events_after(graph_node, output, locale):
        yield event
