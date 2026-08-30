from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.integrations.litellm.llm.client import LiteLLMChatClient
from agentic_shared.integrations.litellm.llm.protocols import ChatClient
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings


class LLMProvider(Provider):
    def __init__(self, settings: LiteLLMChatSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def chat_client(self) -> AsyncIterator[ChatClient]:
        async with LiteLLMChatClient(self._settings) as client:
            yield client
