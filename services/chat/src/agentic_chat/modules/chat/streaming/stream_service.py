import logging
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from agentic_shared.crosscut.i18n import DEFAULT_LOCALE
from agentic_shared.domains.chat.roles import ChatMessageRole
from agentic_shared.domains.persistence.entities import ChatMessage
from agentic_shared.domains.persistence.protocols.chat import (
    ChatMessageReadRepository,
    ChatMessageWriteRepository,
    ChatSessionReadRepository,
    ChatSessionWriteRepository,
)
from agentic_shared.domains.pii_vault.protocols import QueryPiiTokenizationPort
from agentic_shared.domains.pii_vault.reveal_service import VaultRevealService
from agentic_shared.integrations.litellm.analyzer.protocols import Analyzer
from agentic_shared.integrations.litellm.anonymizer.protocols import Anonymizer
from langchain_core.runnables import RunnableConfig

from agentic_chat.core.guard.pii import mask_text
from agentic_chat.core.state import AgentGraphInput, graph_config
from agentic_chat.modules.chat.schemas import ChatMessageOut, to_graph_messages
from agentic_chat.modules.chat.streaming.graph_runner import ChatGraphRunner
from agentic_chat.modules.chat.streaming.session_title import (
    SessionTitleGenerator,
    default_session_title,
)
from agentic_chat.modules.chat.streaming.sse_orchestration import (
    sse_no_checkpoint,
    sse_run_replay,
    sse_run_started,
    sse_session_not_found,
    sse_session_title_updated,
    sse_stream_retry,
    sse_stream_start,
    sse_title_active,
    sse_title_done,
)

logger = logging.getLogger(__name__)

GraphConfig = RunnableConfig


class ChatStreamService:
    def __init__(
        self,
        sessions_read: ChatSessionReadRepository,
        sessions_write: ChatSessionWriteRepository,
        messages_read: ChatMessageReadRepository,
        messages_write: ChatMessageWriteRepository,
        graph_runner: ChatGraphRunner,
        title_generator: SessionTitleGenerator,
        *,
        tenant_id: str,
        query_pii: QueryPiiTokenizationPort | None = None,
        vault_reveal: VaultRevealService | None = None,
        analyzer: Analyzer | None = None,
        anonymizer: Anonymizer | None = None,
    ) -> None:
        self._sessions_read = sessions_read
        self._sessions_write = sessions_write
        self._messages_read = messages_read
        self._messages_write = messages_write
        self._graph_runner = graph_runner
        self._title_generator = title_generator
        self._tenant_id = tenant_id
        self._query_pii = query_pii
        self._vault_reveal = vault_reveal
        self._analyzer = analyzer
        self._anonymizer = anonymizer

    async def _get_messages(self, session_id: uuid.UUID) -> list[ChatMessageOut]:
        rows = await self._messages_read.list_for_session_ordered(session_id)
        return [ChatMessageOut.from_entity(m) for m in rows]

    async def _safe_title_prompt(self, message: str) -> str:
        """Strip PII before the title LLM call; never fall back to plaintext."""
        cleaned = message.strip()
        if not cleaned:
            return cleaned
        if self._query_pii is not None and self._query_pii.enabled:
            return await self._query_pii.tokenize_query(cleaned, tenant_id=self._tenant_id)
        if self._analyzer is not None and self._anonymizer is not None:
            masked = await mask_text(
                cleaned,
                analyzer=self._analyzer,
                anonymizer=self._anonymizer,
            )
            return masked.text
        return cleaned

    async def _generate_session_title(self, message: str, *, locale: str) -> str:
        local_fallback = message.strip()[:120] or default_session_title(locale)
        try:
            prompt = await self._safe_title_prompt(message)
        except Exception:
            logger.exception("session title prompt sanitization failed")
            return local_fallback
        try:
            title = await self._title_generator.generate(prompt, locale=locale)
        except Exception:
            logger.exception("session title generation failed")
            return local_fallback
        if (
            self._vault_reveal is not None
            and self._query_pii is not None
            and self._query_pii.enabled
        ):
            try:
                title = await self._vault_reveal.reveal_text(title)
            except Exception:
                logger.exception("session title detokenize failed")
        return title

    async def stream_response(
        self,
        session_id: uuid.UUID,
        message: str,
        run_id: str | None = None,
        *,
        locale: str = DEFAULT_LOCALE,
    ) -> AsyncIterator[str]:
        """SSE events: token chunks, then done with citations."""
        chat_session = await self._sessions_read.get_by_id(session_id)
        if not chat_session:
            logger.warning("chat session not found session_id=%s", session_id)
            yield sse_session_not_found(locale)
            return

        resolved_run_id = run_id or str(uuid.uuid4())
        logger.info(
            "chat stream started session_id=%s tenant_id=%s run_id=%s",
            session_id,
            self._tenant_id,
            resolved_run_id,
        )
        user_msg = ChatMessage(session_id=session_id, role=ChatMessageRole.USER, content=message)
        await self._messages_write.add(user_msg)
        chat_session.updated_at = datetime.now(UTC)
        await self._sessions_write.update(chat_session)

        thread_id = _thread_id(self._tenant_id, session_id, resolved_run_id)
        config: GraphConfig = graph_config(thread_id=thread_id)
        history = await self._get_messages(session_id)
        graph_messages = to_graph_messages(history)
        user_count = sum(1 for m in history if m.role == ChatMessageRole.USER)
        is_first_turn = user_count == 1 and SessionTitleGenerator.is_default_title(
            chat_session.title
        )

        yield sse_run_started(resolved_run_id)
        yield sse_stream_start(locale)

        if is_first_turn:
            yield sse_title_active(locale)
            new_title = await self._generate_session_title(message, locale=locale)
            chat_session.title = new_title
            await self._sessions_write.update(chat_session)
            yield sse_title_done(locale, new_title)
            yield sse_session_title_updated(str(session_id), new_title)

        input_state = AgentGraphInput(
            messages=graph_messages,
            thread_id=thread_id,
            locale=locale,
            tenant_id=self._tenant_id,
        ).as_state()
        async for event in self._graph_runner.stream_execute(
            session_id, config, input_state=input_state, locale=locale
        ):
            yield event

    async def stream_replay(
        self,
        session_id: uuid.UUID,
        run_id: str,
        query: str,
        checkpoint_id: str | None = None,
        *,
        locale: str = DEFAULT_LOCALE,
    ) -> AsyncIterator[str]:
        chat_session = await self._sessions_read.get_by_id(session_id)
        if not chat_session:
            logger.warning("chat session not found session_id=%s", session_id)
            yield sse_session_not_found(locale)
            return

        thread_id = _thread_id(self._tenant_id, session_id, run_id)
        base_config: GraphConfig = graph_config(thread_id=thread_id)

        resolved_checkpoint = checkpoint_id
        if not resolved_checkpoint:
            resolved_checkpoint = await self._graph_runner.find_start_checkpoint(base_config)
            if not resolved_checkpoint:
                logger.warning("chat replay missing checkpoint session_id=%s", session_id)
                yield sse_no_checkpoint(locale)
                return

        await self._messages_write.delete_last_assistant(session_id)
        chat_session.updated_at = datetime.now(UTC)
        await self._sessions_write.update(chat_session)

        config: GraphConfig = graph_config(thread_id=thread_id, checkpoint_id=resolved_checkpoint)

        yield sse_run_replay(run_id, resolved_checkpoint)
        yield sse_stream_retry(locale)
        logger.info(
            "chat replay started session_id=%s tenant_id=%s run_id=%s",
            session_id,
            self._tenant_id,
            run_id,
        )

        async for event in self._graph_runner.stream_execute(
            session_id, config, input_state=None, locale=locale
        ):
            yield event


def _thread_id(tenant_id: str, session_id: uuid.UUID, run_id: str) -> str:
    return f"{tenant_id}:{session_id}:{run_id}"
