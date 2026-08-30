from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.integrations.litellm.analyzer.client import AnalyzerClient
from agentic_shared.integrations.litellm.analyzer.protocols import Analyzer
from agentic_shared.integrations.litellm.analyzer.settings import AnalyzerSettings


class AnalyzerProvider(Provider):
    def __init__(self, settings: AnalyzerSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def analyzer(self) -> AsyncIterator[Analyzer]:
        async with AnalyzerClient(self._settings) as client:
            yield client
