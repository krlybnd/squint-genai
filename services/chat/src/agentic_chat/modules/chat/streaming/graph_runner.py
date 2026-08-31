import json
import logging
import uuid
from collections.abc import AsyncIterator, Sequence
from typing import Any, Literal, cast

from agentic_shared.crosscut.i18n import DEFAULT_LOCALE, t
from agentic_shared.domains.chat.roles import ChatMessageRole
from agentic_shared.domains.persistence.entities import ChatMessage
from agentic_shared.domains.persistence.protocols.chat import ChatMessageWriteRepository
from agentic_shared.domains.pii_vault.reveal_service import (
    StreamingVaultReveal,
    VaultRevealService,
    collect_vault_tokens,
)
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
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
GraphNodeUpdates = dict[str, AgentStateUpdate]
AstreamItem = tuple[Literal["updates"], GraphNodeUpdates] | tuple[Literal["custom"], str]


class ChatGraphRunner:
    def __init__(
        self,
        graph: ChatCompiledGraph,
        messages_write: ChatMessageWriteRepository,
        *,
        vault_reveal: VaultRevealService | None = None,
        pii_vault: PiiVaultSettings | None = None,
    ) -> None:
        self._graph = graph
        self._messages_write = messages_write
        self._vault_reveal = vault_reveal
        self._pii_vault = pii_vault or PiiVaultSettings()

    def _astream(
        self,
        input_state: AgentGraphInputState | None,
        config: GraphConfig,
    ) -> AsyncIterator[AstreamItem]:
        return cast(
            AsyncIterator[AstreamItem],
            self._graph.astream(
                input_state,
                config=config,
                stream_mode=["updates", "custom"],
            ),
        )

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
        extra_tokens: Sequence[str] = (),
    ) -> AsyncIterator[str]:
        if (
            self._pii_vault.enabled
            and self._pii_vault.sse_detokenize_enabled
            and self._vault_reveal is not None
        ):
            answer = await self._vault_reveal.reveal_text(
                answer, marked=True, extra_tokens=extra_tokens
            )
            citations = await self._vault_reveal.reveal_citations(citations, marked=True)
        await self._persist_assistant(session_id, answer, citations)
        yield sse_done(DoneEventData(answer=answer, citations=citations))

    async def _emit_stream_token(
        self,
        token: str,
        stream_reveal: StreamingVaultReveal | None,
    ) -> AsyncIterator[str]:
        if stream_reveal is None:
            if token:
                yield sse_token(TokenEventData(content=token))
            return
        revealed = await stream_reveal.feed(token)
        if revealed:
            yield sse_token(TokenEventData(content=revealed))

    async def _flush_stream_tokens(
        self,
        stream_reveal: StreamingVaultReveal | None,
    ) -> AsyncIterator[str]:
        if stream_reveal is None:
            return
        remainder = await stream_reveal.flush()
        if remainder:
            yield sse_token(TokenEventData(content=remainder))

    async def stream_execute(
        self,
        session_id: uuid.UUID,
        config: GraphConfig,
        *,
        input_state: AgentGraphInputState | None,
        locale: str = DEFAULT_LOCALE,
    ) -> AsyncIterator[str]:
        final_state: AgentStateUpdate = {}
        chunk_tokens: set[str] = set()
        stream_reveal: StreamingVaultReveal | None = None
        if (
            self._pii_vault.enabled
            and self._pii_vault.sse_detokenize_enabled
            and self._vault_reveal is not None
        ):
            stream_reveal = StreamingVaultReveal(self._vault_reveal, marked=True)
        try:
            async for item in self._astream(input_state, config):
                match item:
                    case ("custom", token) if token != "":
                        async for event in self._emit_stream_token(token, stream_reveal):
                            yield event
                    case ("updates", updates):
                        for node, node_output in updates.items():
                            final_state.update(node_output)
                            chunk_tokens.update(collect_vault_tokens(node_output))
                            checkpoint_id = await self._checkpoint_id(config)
                            async for event in events_for_node(
                                node, node_output, checkpoint_id, locale
                            ):
                                yield event
                            if node not in (AgentGraphNode.GENERATE, AgentGraphNode.BLOCK):
                                continue
                            answer = str(node_output.get("answer", ""))
                            citations = citation_states(citations_from_output(node_output))
                            logger.info(
                                "chat graph completed session_id=%s node=%s citations=%d",
                                session_id,
                                node,
                                len(citations),
                            )
                            async for event in self._flush_stream_tokens(stream_reveal):
                                yield event
                            extra_tokens = sorted(
                                chunk_tokens | set(collect_vault_tokens(final_state, citations))
                            )
                            logger.info(
                                "chat vault marks session_id=%s tokens=%d",
                                session_id,
                                len(extra_tokens),
                            )
                            async for event in self._finish_with_answer(
                                session_id,
                                answer,
                                citations,
                                extra_tokens=extra_tokens,
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
            async for event in self._flush_stream_tokens(stream_reveal):
                yield event
            extra_tokens = sorted(chunk_tokens | set(collect_vault_tokens(final_state, citations)))
            async for event in self._finish_with_answer(
                session_id,
                answer,
                citations,
                extra_tokens=extra_tokens,
            ):
                yield event
