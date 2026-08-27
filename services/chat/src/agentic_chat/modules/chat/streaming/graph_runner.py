import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any, cast

from agentic_shared.core.i18n import DEFAULT_LOCALE, t
from agentic_shared.domains.chat.roles import ChatMessageRole
from agentic_shared.domains.persistence.entities import ChatMessage
from agentic_shared.domains.persistence.protocols.chat import ChatMessageWriteRepository
from langchain_core.runnables import RunnableConfig

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.state import (
    AgentGraphInputState,
    AgentStateUpdate,
    ChatCompiledGraph,
    citation_states,
    citations_from_output,
)
from agentic_chat.modules.chat.streaming.sse_events import (
    DoneEventData,
    ErrorEventData,
    TokenEventData,
    sse_done,
    sse_error,
    sse_token,
)
from agentic_chat.modules.chat.streaming.sse_reasoning import events_for_node

logger = logging.getLogger(__name__)

GraphConfig = RunnableConfig


class ChatGraphRunner:
    _simulated_token_chars = 24

    def __init__(
        self,
        graph: ChatCompiledGraph,
        messages_write: ChatMessageWriteRepository,
    ) -> None:
        self._graph = graph
        self._messages_write = messages_write

    def _simulated_token_chunks(self, answer: str) -> list[str]:
        """Split a finished answer for SSE without destroying whitespace or punctuation."""
        if not answer:
            return []
        size = self._simulated_token_chars
        return [answer[i : i + size] for i in range(0, len(answer), size)]

    async def find_start_checkpoint(self, config: GraphConfig) -> str | None:
        async for state in self._graph.aget_state_history(config):
            if state.next == ("__start__",):
                checkpoint_id = state.config.get("configurable", {}).get("checkpoint_id")
                return str(checkpoint_id) if checkpoint_id else None
        return None

    async def _checkpoint_id(self, config: GraphConfig) -> str | None:
        state = await self._graph.aget_state(config)
        raw = state.config.get("configurable", {}).get("checkpoint_id")
        return str(raw) if raw else None

    async def _persist_assistant(
        self,
        session_id: uuid.UUID,
        answer: str,
        citations: list[dict[str, Any]],
    ) -> None:
        assistant_msg = ChatMessage(
            session_id=session_id,
            role=ChatMessageRole.ASSISTANT,
            content=answer,
            citations_json=json.dumps(citations),
        )
        await self._messages_write.add(assistant_msg)

    async def _finish_with_answer(
        self,
        session_id: uuid.UUID,
        answer: str,
        citations: list[dict[str, Any]],
        *,
        stream_tokens: bool,
    ) -> AsyncIterator[str]:
        if stream_tokens:
            for chunk in self._simulated_token_chunks(answer):
                yield sse_token(TokenEventData(content=chunk))
        await self._persist_assistant(session_id, answer, citations)
        yield sse_done(DoneEventData(answer=answer, citations=citations))

    async def stream_execute(
        self,
        session_id: uuid.UUID,
        config: GraphConfig,
        *,
        input_state: AgentGraphInputState | None,
        locale: str = DEFAULT_LOCALE,
    ) -> AsyncIterator[str]:
        final_state: AgentStateUpdate = {}
        try:
            async for update in self._graph.astream(
                input_state,
                config=config,
                stream_mode="updates",
            ):
                for node, output in update.items():
                    if not isinstance(output, dict):
                        continue
                    node_output = cast(AgentStateUpdate, output)
                    final_state.update(node_output)
                    checkpoint_id = await self._checkpoint_id(config)
                    async for event in events_for_node(node, node_output, checkpoint_id, locale):
                        yield event

                    if node in (AgentGraphNode.GENERATE, AgentGraphNode.BLOCK):
                        answer = str(node_output.get("answer", ""))
                        citations = citation_states(citations_from_output(node_output))
                        logger.info(
                            "chat graph completed session_id=%s node=%s citations=%d",
                            session_id,
                            node,
                            len(citations),
                        )
                        async for event in self._finish_with_answer(
                            session_id,
                            answer,
                            citations,
                            stream_tokens=True,
                        ):
                            yield event
                        return
        except Exception as exc:
            logger.exception("chat graph execution failed session_id=%s", session_id)
            yield sse_error(
                ErrorEventData(message=t("error.chat_failed", locale, detail=str(exc))),
            )
            return

        answer = str(final_state.get("answer", ""))
        if answer:
            citations = citation_states(citations_from_output(final_state))
            async for event in self._finish_with_answer(
                session_id,
                answer,
                citations,
                stream_tokens=False,
            ):
                yield event
