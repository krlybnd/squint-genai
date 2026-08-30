from openai import AsyncOpenAI

from agentic_shared.integrations.core.client import IntegrationClient
from agentic_shared.integrations.litellm.core.settings import LiteLLMSettings
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings


class LiteLLMEmbeddingClient(IntegrationClient[LiteLLMEmbeddingSettings]):
    """Embeddings against LiteLLM (OpenAI-compatible HTTP API)."""

    def __init__(self, llm: LiteLLMSettings, embedding: LiteLLMEmbeddingSettings) -> None:
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
            self._logger.debug("%s health check failed", self.title, exc_info=True)
            return False

    async def aclose(self) -> None:
        try:
            await self._client.close()
        finally:
            await super().aclose()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self._logger.info("embed model=%s texts=%d", self._model, len(texts))
        response = await self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]
