import logging

from openai import AsyncOpenAI

from agentic_shared.core.resources.client import BaseResourceClient
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings

logger = logging.getLogger(__name__)


class OpenAIEmbeddingClient(BaseResourceClient[EmbeddingSettings]):
    """Embeddings via OpenAI SDK (base URL points at LiteLLM or OpenAI)."""

    def __init__(self, llm: LLMSettings, embedding: EmbeddingSettings) -> None:
        super().__init__(embedding)
        self._llm = llm
        self._model = embedding.embedding_model
        self._client = AsyncOpenAI(
            base_url=f"{llm.litellm_base_url.rstrip('/')}/v1",
            api_key=llm.proxy_api_key,
        )

    async def health_check(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            logger.debug("embedding health check failed", exc_info=True)
            return False

    async def aclose(self) -> None:
        try:
            await self._client.close()
        finally:
            await super().aclose()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]
