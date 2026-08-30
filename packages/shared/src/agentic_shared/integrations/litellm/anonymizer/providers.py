from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.integrations.litellm.anonymizer.client import AnonymizerClient
from agentic_shared.integrations.litellm.anonymizer.protocols import Anonymizer
from agentic_shared.integrations.litellm.anonymizer.settings import AnonymizerSettings


class AnonymizerProvider(Provider):
    def __init__(self, settings: AnonymizerSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def anonymizer(self) -> AsyncIterator[Anonymizer]:
        async with AnonymizerClient(self._settings) as client:
            yield client
