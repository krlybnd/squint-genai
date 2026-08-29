from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader
from agentic_shared.domains.retrieval.providers import AsyncRetrievalProvider
from dishka import Scope, provide

from agentic_api.modules.retrieval.service import RetrievalApiService
from agentic_api.settings import ApiSettings


class RetrievalProvider(AsyncRetrievalProvider):
    def __init__(self, settings: ApiSettings) -> None:
        super().__init__(
            settings.llm,
            settings.embedding,
            settings.rerank,
        )
        self._settings = settings

    @provide(scope=Scope.APP)
    def retrieval_api(self, async_retrieval_reader: AsyncRetrievalReader) -> RetrievalApiService:
        return RetrievalApiService(async_retrieval_reader, self._settings)
