from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.integrations.litellm.guard.client import GuardClient
from agentic_shared.integrations.litellm.guard.protocols import Guard
from agentic_shared.integrations.litellm.guard.settings import GuardSettings


class GuardProvider(Provider):
    def __init__(self, settings: GuardSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def guard(self) -> AsyncIterator[Guard]:
        async with GuardClient(self._settings) as client:
            yield client
