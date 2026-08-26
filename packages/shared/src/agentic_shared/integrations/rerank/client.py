import httpx

from agentic_shared.core.resources.client import BaseResourceClient
from agentic_shared.integrations.llm.settings import LLMSettings
from agentic_shared.integrations.rerank.settings import RerankSettings


class RerankClient(BaseResourceClient[RerankSettings]):
    """Cross-encoder rerank via LiteLLM `/rerank` (Cohere-compatible)."""

    def __init__(self, llm: LLMSettings, settings: RerankSettings) -> None:
        super().__init__(settings)
        self._llm = llm

    async def health_check(self) -> bool:
        if not self._settings.rerank_enabled:
            return True
        try:
            self.rerank("health", ["ok"], top_n=1)
            return True
        except httpx.HTTPError:
            return False

    def rerank(self, query: str, documents: list[str], *, top_n: int) -> list[int]:
        if not self._settings.rerank_enabled or not documents:
            return list(range(min(top_n, len(documents))))
        if len(documents) == 1:
            return [0]

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self._llm.litellm_base_url.rstrip('/')}/rerank",
                headers={"Authorization": f"Bearer {self._llm.proxy_api_key}"},
                json={
                    "model": self._settings.rerank_model,
                    "query": query,
                    "documents": documents,
                    "top_n": min(top_n, len(documents)),
                },
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_rerank_indices(data, top_n=top_n, document_count=len(documents))

    async def rerank_async(self, query: str, documents: list[str], *, top_n: int) -> list[int]:
        if not self._settings.rerank_enabled or not documents:
            return list(range(min(top_n, len(documents))))
        if len(documents) == 1:
            return [0]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._llm.litellm_base_url.rstrip('/')}/rerank",
                headers={"Authorization": f"Bearer {self._llm.proxy_api_key}"},
                json={
                    "model": self._settings.rerank_model,
                    "query": query,
                    "documents": documents,
                    "top_n": min(top_n, len(documents)),
                },
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_rerank_indices(data, top_n=top_n, document_count=len(documents))

    @staticmethod
    def _parse_rerank_indices(data: dict, *, top_n: int, document_count: int) -> list[int]:
        results = data.get("results", [])
        if not results:
            return list(range(min(top_n, document_count)))
        return [int(item["index"]) for item in results]
