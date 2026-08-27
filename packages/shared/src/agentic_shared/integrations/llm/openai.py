import logging
from typing import Any, cast

import httpx
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

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

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        stream: bool = False,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> ChatCompletionResult | Any:
        resolved = model or self._model
        logger.debug(
            "chat completion model=%s messages=%d stream=%s",
            resolved,
            len(messages),
            stream,
        )
        payload = cast(list[ChatCompletionMessageParam], messages)
        if stream:
            return await self._client.chat.completions.create(
                model=resolved,
                messages=payload,
                temperature=temperature,
                stream=True,
            )
        response = await self._client.chat.completions.create(
            model=resolved,
            messages=payload,
            temperature=temperature,
            stream=False,
        )
        return ChatCompletionResult.from_api_response(response.model_dump())
