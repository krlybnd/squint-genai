from collections.abc import Sequence

import httpx

from agentic_shared.integrations.core.client import IntegrationClient
from agentic_shared.integrations.litellm.core.settings import LiteLLMSettings
from agentic_shared.integrations.litellm.rerank.errors import RerankError
from agentic_shared.integrations.litellm.rerank.models import RerankHit, RerankResult
from agentic_shared.integrations.litellm.rerank.settings import LiteLLMRerankSettings


class LiteLLMRerankClient(IntegrationClient[LiteLLMRerankSettings]):
    """Rerank against LiteLLM (Cohere-shaped HTTP `/rerank`)."""

    def __init__(self, llm: LiteLLMSettings, rerank: LiteLLMRerankSettings) -> None:
        super().__init__(rerank)
        self._llm = llm
        self._model = rerank.rerank_model
        self._http = httpx.AsyncClient(
            base_url=llm.litellm_base_url.rstrip("/"),
            timeout=httpx.Timeout(30.0, connect=5.0),
            headers={"Authorization": f"Bearer {llm.proxy_api_key}"},
        )

    @property
    def enabled(self) -> bool:
        return self._settings.rerank_enabled

    @property
    def model(self) -> str:
        return self._model

    async def health_check(self) -> bool:
        try:
            response = await self._http.get("/health")
            return response.status_code == 200
        except httpx.HTTPError:
            self._logger.debug("%s health check failed", self.title, exc_info=True)
            return False

    async def aclose(self) -> None:
        try:
            await self._http.aclose()
        finally:
            await super().aclose()

    async def rerank(
        self,
        query: str,
        documents: Sequence[str],
        *,
        top_n: int,
    ) -> list[RerankHit]:
        if not self.enabled or not query.strip() or not documents or top_n <= 0:
            return []
        self._logger.info(
            "rerank model=%s docs=%d top_n=%d",
            self._model,
            len(documents),
            top_n,
        )
        clipped = self._clip_documents(documents)
        try:
            response = await self._http.post(
                "/rerank",
                json={
                    "model": self._model,
                    "query": query,
                    "documents": clipped,
                    "top_n": top_n,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RerankError(f"LiteLLM /rerank failed: {exc}") from exc
        return RerankResult.from_api_response(response.json()).hits

    def _clip_documents(self, documents: Sequence[str]) -> list[str]:
        limit = self._settings.rerank_max_doc_chars
        if limit <= 0:
            return list(documents)
        return [doc[:limit] for doc in documents]
