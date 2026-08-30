from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from agentic_shared.integrations.litellm.llm.models import ChatCompletionResult


@runtime_checkable
class ChatClient(Protocol):
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> ChatCompletionResult: ...

    def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> AsyncIterator[str]: ...
