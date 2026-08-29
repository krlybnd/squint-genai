from __future__ import annotations

import logging
from typing import cast

from agentic_shared.core.domain_errors import BadRequestError, NotFoundError
from agentic_shared.core.i18n import DEFAULT_LOCALE, t
from agentic_shared.domains.retrieval.protocols.chunks import ChunkReadRepository
from agentic_shared.infrastructure.vector.enums import QdrantPointType

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
        chunk_read: ChunkReadRepository,
        graph: CommentCompiledGraph,
    ) -> None:
        self._graph = graph
        self._tenant_id = tenant_id
        self._chunk_read = chunk_read

    async def create_chunk_comment(
        self,
        chunk_id: str,
        body: CreateChunkCommentRequest,
        *,
        user_id: str | None,
        locale: str = DEFAULT_LOCALE,
    ) -> ChunkCommentOut:
        chunk_payload = self._chunk_read.get_by_id(chunk_id, tenant_id=self._tenant_id)
        if chunk_payload is None:
            raise NotFoundError("Chunk not found")
        if chunk_payload.point_type == QdrantPointType.COMMENT:
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

        saved_payload = self._chunk_read.get_by_id(chunk_id, tenant_id=self._tenant_id)
        comments = [] if saved_payload is None else saved_payload.comments
        comment_id = state.get("comment_id") or ""
        logger.info(
            "comment created chunk_id=%s comment_id=%s tenant_id=%s",
            chunk_id,
            comment_id,
            self._tenant_id,
        )
        saved = next((comment for comment in comments if comment.comment_id == comment_id), None)
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
        payload = self._chunk_read.get_by_id(chunk_id, tenant_id=self._tenant_id)
        if payload is None:
            raise NotFoundError("Chunk not found")
        return [ChunkCommentOut.from_stored(chunk_id, comment) for comment in payload.comments]
