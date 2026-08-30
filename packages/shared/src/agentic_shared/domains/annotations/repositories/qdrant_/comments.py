import logging

from agentic_shared.domains.annotations.models import ChunkComment, CommentPointPayload
from agentic_shared.domains.annotations.protocols.comments import (
    CommentReadRepository,
    CommentWriteRepository,
)
from agentic_shared.domains.retrieval.models import ChunkPointPayload
from agentic_shared.infrastructure.vector.qdrant.client import QdrantClient
from agentic_shared.infrastructure.vector.qdrant.reader import QdrantVectorReader
from agentic_shared.infrastructure.vector.qdrant.writer import QdrantVectorWriter

logger = logging.getLogger(__name__)


class QdrantCommentReadRepository(CommentReadRepository):
    def __init__(self, client: QdrantClient) -> None:
        self._chunks = QdrantVectorReader[ChunkPointPayload](client, ChunkPointPayload)

    def list_for_chunk(self, chunk_id: str, *, tenant_id: str) -> list[ChunkComment]:
        chunk = self._chunks.get_by_id(chunk_id, tenant_id=tenant_id)
        if chunk is None:
            return []
        return list(chunk.comments)


class QdrantCommentWriteRepository(QdrantVectorWriter[CommentPointPayload], CommentWriteRepository):
    def __init__(self, client: QdrantClient) -> None:
        super().__init__(client, CommentPointPayload)
        self._chunks = QdrantVectorReader[ChunkPointPayload](client, ChunkPointPayload)

    def append_to_chunk(self, chunk_id: str, comment: ChunkComment, *, tenant_id: str) -> None:
        chunk = self._chunks.get_by_id(chunk_id, tenant_id=tenant_id)
        if chunk is None:
            raise ValueError(f"chunk not found: {chunk_id}")
        comments = list(chunk.comments)
        comments.append(comment)
        self.set_payload(
            [chunk_id],
            {"comments": [item.model_dump(mode="json") for item in comments]},
        )
