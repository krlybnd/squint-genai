import logging
from collections.abc import AsyncIterator
from typing import cast

import httpx
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam

from agentic_shared.core.resources.client import BaseResourceClient
from agentic_shared.integrations.llm.models import ChatCompletionResult
from agentic_shared.integrations.llm.settings import LLMSettings

logger = logging.getLogger(__name__)


class OpenAIChatClient(BaseResourceClient[LLMSettings]):
    """Chat completions via OpenAI SDK (base URL points at LiteLLM or OpenAI)."""

    def __init__(self, settings: LLMSettings) -> None:
        super().__init__(settings)
        self._model = settings.litellm_model
        self._client = AsyncOpenAI(
            base_url=f"{settings.litellm_base_url.rstrip('/')}/v1",
            api_key=settings.proxy_api_key,
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self._settings.litellm_base_url.rstrip('/')}/health",
                    headers={"Authorization": f"Bearer {self._settings.proxy_api_key}"},
                )
                return response.status_code == 200
        except httpx.HTTPError:
            logger.debug("llm health check failed", exc_info=True)
            return False

    async def aclose(self) -> None:
        try:
            await self._client.close()
        finally:
            await super().aclose()

    def _messages(self, messages: list[dict[str, str]]) -> list[ChatCompletionMessageParam]:
        return cast(list[ChatCompletionMessageParam], messages)

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> ChatCompletionResult:
        resolved = model or self._model
        logger.debug("chat completion model=%s messages=%d", resolved, len(messages))
        response = await self._client.chat.completions.create(
            model=resolved,
            messages=self._messages(messages),
            temperature=temperature,
            stream=False,
        )
        return ChatCompletionResult.from_api_response(response.model_dump())

    async def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> AsyncIterator[str]:
        resolved = model or self._model
        logger.debug("chat completion stream model=%s messages=%d", resolved, len(messages))
        stream: AsyncStream[ChatCompletionChunk] = await self._client.chat.completions.create(
            model=resolved,
            messages=self._messages(messages),
            temperature=temperature,
            stream=True,
        )
        async for event in stream:
            if not event.choices:
                continue
            content = event.choices[0].delta.content
            if content is None:
                continue
            yield content
