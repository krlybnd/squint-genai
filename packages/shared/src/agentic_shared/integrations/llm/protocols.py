from typing import Any, Protocol, runtime_checkable

from agentic_shared.integrations.llm.models import ChatCompletionResult


@runtime_checkable
class ChatClient(Protocol):
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        stream: bool = False,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> ChatCompletionResult | Any: ...
