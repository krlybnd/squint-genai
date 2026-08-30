from qdrant_client import QdrantClient as QdrantSdkClient

from agentic_shared.infrastructure.core.client import InfrastructureClient
from agentic_shared.infrastructure.vector.qdrant.settings import QdrantSettings


class QdrantClient(InfrastructureClient[QdrantSettings]):
    """Qdrant connection lifecycle. I/O lives on reader/writer wrappers."""

    def __init__(self, settings: QdrantSettings) -> None:
        super().__init__(settings)
        self._sdk = QdrantSdkClient(url=settings.qdrant_url)

    async def health_check(self) -> bool:
        return self.is_available()

    def close(self) -> None:
        try:
            self._sdk.close()
        finally:
            super().close()

    def is_available(self) -> bool:
        try:
            self._sdk.get_collections()
            return True
        except Exception:
            self._logger.debug("%s health check failed", self.title, exc_info=True)
            return False

    @property
    def default_top_k(self) -> int:
        return self._settings.top_k

    @property
    def candidate_top_k(self) -> int:
        return self._settings.candidate_top_k

    @property
    def sparse_model(self) -> str:
        return self._settings.sparse_model

    @property
    def collection_name(self) -> str:
        return self._settings.qdrant_collection

    @property
    def dense_vector_name(self) -> str:
        return self._settings.dense_vector_name

    @property
    def sparse_vector_name(self) -> str:
        return self._settings.sparse_vector_name
