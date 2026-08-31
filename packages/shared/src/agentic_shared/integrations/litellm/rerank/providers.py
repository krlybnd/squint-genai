from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.integrations.litellm.core.settings import LiteLLMSettings
from agentic_shared.integrations.litellm.rerank.client import LiteLLMRerankClient
from agentic_shared.integrations.litellm.rerank.protocols import RerankPort
from agentic_shared.integrations.litellm.rerank.settings import LiteLLMRerankSettings


class RerankProvider(Provider):
    def __init__(self, llm: LiteLLMSettings, rerank: LiteLLMRerankSettings) -> None:
        super().__init__()
        self._llm = llm
        self._rerank = rerank

    @provide(scope=Scope.APP)
    async def reranker(self) -> AsyncIterator[RerankPort]:
        async with LiteLLMRerankClient(self._llm, self._rerank) as client:
            yield client
