from typing import Protocol, runtime_checkable

from agentic_shared.domains.annotations.models import ChunkComment, CommentPointPayload
from agentic_shared.infrastructure.vector.core.protocols import VectorWriter


@runtime_checkable
class CommentReadRepository(Protocol):
    def list_for_chunk(self, chunk_id: str, *, tenant_id: str) -> list[ChunkComment]: ...


@runtime_checkable
class CommentWriteRepository(VectorWriter[CommentPointPayload], Protocol):
    def append_to_chunk(self, chunk_id: str, comment: ChunkComment, *, tenant_id: str) -> None: ...
