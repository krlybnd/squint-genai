import unittest
from unittest.mock import AsyncMock, Mock

from agentic_shared.domains.domain_errors import BadRequestError
from agentic_shared.domains.retrieval.models import ChunkPointPayload
from agentic_shared.infrastructure.vector.qdrant.enums import QdrantPointType

from agentic_api.modules.annotations.schemas import CreateChunkCommentRequest
from agentic_api.modules.annotations.service import AnnotationService, CommentRejectedError


class TestAnnotationService(unittest.IsolatedAsyncioTestCase):
    def _service(self) -> AnnotationService:
        return AnnotationService(
            tenant_id="tenant-1",
            chunk_read=Mock(),
            graph=AsyncMock(),
        )

    async def test_create_chunk_comment_rejects_comment_points(self) -> None:
        # Arrange
        service = self._service()
        service._chunk_read.get_by_id.return_value = ChunkPointPayload(
            point_type=QdrantPointType.COMMENT,
        )
        body = CreateChunkCommentRequest(
            selected_text="excerpt",
            comment_text="looks good",
        )

        # Act / Assert
        with self.assertRaises(BadRequestError):
            await service.create_chunk_comment("chunk-1", body, user_id="user-1")

        # Assert
        service._graph.ainvoke.assert_not_awaited()

    async def test_create_chunk_comment_raises_when_graph_rejects(self) -> None:
        # Arrange
        service = self._service()
        service._chunk_read.get_by_id.return_value = ChunkPointPayload(
            point_type=QdrantPointType.CHUNK,
            doc_id="doc-1",
        )
        service._graph.ainvoke.return_value = {
            "approved": False,
            "rejection_reason": "Policy violation",
        }
        body = CreateChunkCommentRequest(
            selected_text="excerpt",
            comment_text="looks good",
        )

        # Act / Assert
        with self.assertRaises(CommentRejectedError) as ctx:
            await service.create_chunk_comment("chunk-1", body, user_id="user-1")

        # Assert
        self.assertEqual(ctx.exception.reason, "Policy violation")


if __name__ == "__main__":
    unittest.main()
