from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.core.resources.client import open_resource
from agentic_shared.integrations.llm.openai import OpenAIChatClient
from agentic_shared.integrations.llm.protocols import ChatClient
from agentic_shared.integrations.llm.settings import LLMSettings


class LLMProvider(Provider):
    def __init__(self, settings: LLMSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def chat_client(self) -> AsyncIterator[ChatClient]:
        async with open_resource(OpenAIChatClient(self._settings)) as client:
            yield client
