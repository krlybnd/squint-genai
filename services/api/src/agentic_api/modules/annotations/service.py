from __future__ import annotations

import logging
from typing import Any, cast

from agentic_shared.core.domain_errors import BadRequestError, NotFoundError
from agentic_shared.core.i18n import DEFAULT_LOCALE, t
from agentic_shared.infrastructure.vector.comments import normalize_comments
from agentic_shared.infrastructure.vector.enums import QdrantPointType
from agentic_shared.infrastructure.vector.protocols import QdrantReader
from agentic_shared.infrastructure.vector.types import ChunkPointPayload

from agentic_api.modules.annotations.schemas import ChunkCommentOut, CreateChunkCommentRequest
from agentic_api.modules.annotations.state import (
    CommentCompiledGraph,
    CommentGraphInput,
    CommentState,
)

logger = logging.getLogger(__name__)


class CommentRejectedError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _as_chunk_payload(raw: dict[str, Any]) -> ChunkPointPayload:
    return cast(ChunkPointPayload, raw)


def _rejection_reason(state: CommentState, locale: str) -> str:
    reason = state.get("rejection_reason")
    if reason:
        return reason
    return t("annotations.rejection.default", locale)


class AnnotationService:
    def __init__(
        self,
        *,
        tenant_id: str,
        qdrant_read: QdrantReader,
        graph: CommentCompiledGraph,
    ) -> None:
        self._graph = graph
        self._tenant_id = tenant_id
        self._qdrant_read = qdrant_read

    async def create_chunk_comment(
        self,
        chunk_id: str,
        body: CreateChunkCommentRequest,
        *,
        user_id: str | None,
        locale: str = DEFAULT_LOCALE,
    ) -> ChunkCommentOut:
        raw_payload = self._qdrant_read.retrieve_point(chunk_id, tenant_id=self._tenant_id)
        if raw_payload is None:
            raise NotFoundError("Chunk not found")
        chunk_payload = _as_chunk_payload(raw_payload)
        if chunk_payload.get("point_type") == QdrantPointType.COMMENT:
            raise BadRequestError("Cannot comment on a comment point")

        graph_input = CommentGraphInput(
            chunk_id=chunk_id,
            selected_text=body.selected_text.strip(),
            comment_text=body.comment_text.strip(),
            user_id=user_id,
            chunk_payload=chunk_payload,
            tenant_id=self._tenant_id,
            locale=locale,
        )
        result = await self._graph.ainvoke(graph_input.as_state())
        if not isinstance(result, dict):
            raise TypeError("comment graph must return a dict state")
        state = cast(CommentState, result)

        if not state.get("approved"):
            reason = _rejection_reason(state, locale)
            logger.info(
                "comment rejected chunk_id=%s tenant_id=%s",
                chunk_id,
                self._tenant_id,
            )
            raise CommentRejectedError(reason)

        comments = normalize_comments(
            self._qdrant_read.retrieve_point(chunk_id, tenant_id=self._tenant_id)
        )
        comment_id = state.get("comment_id") or ""
        logger.info(
            "comment created chunk_id=%s comment_id=%s tenant_id=%s",
            chunk_id,
            comment_id,
            self._tenant_id,
        )
        saved = next((c for c in comments if c.comment_id == comment_id), None)
        if saved:
            return ChunkCommentOut.from_stored(chunk_id, saved)

        return ChunkCommentOut(
            comment_id=comment_id,
            chunk_id=chunk_id,
            selected_text=body.selected_text,
            comment_text=body.comment_text,
            user_id=user_id,
            created_at="",
        )

    def list_chunk_comments(self, chunk_id: str) -> list[ChunkCommentOut]:
        payload = self._qdrant_read.retrieve_point(chunk_id, tenant_id=self._tenant_id)
        if payload is None:
            raise NotFoundError("Chunk not found")
        return [
            ChunkCommentOut.from_stored(chunk_id, comment)
            for comment in normalize_comments(payload)
        ]
