from __future__ import annotations

from collections.abc import Sequence

import httpx

from agentic_shared.integrations.core.client import IntegrationClient
from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity
from agentic_shared.integrations.litellm.anonymizer.errors import AnonymizerError
from agentic_shared.integrations.litellm.anonymizer.models import AnonymizeResult
from agentic_shared.integrations.litellm.anonymizer.settings import AnonymizerSettings


class AnonymizerClient(IntegrationClient[AnonymizerSettings]):
    """Anonymizer HTTP client (PII redact)."""

    def __init__(self, settings: AnonymizerSettings) -> None:
        super().__init__(settings)
        self._http = httpx.AsyncClient(
            base_url=settings.anonymizer_api_base.rstrip("/"),
            timeout=httpx.Timeout(60.0, connect=5.0),
        )

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

    async def anonymize(
        self,
        text: str,
        analyzer_results: Sequence[AnalyzerEntity],
    ) -> AnonymizeResult:
        self._logger.info(
            "anonymize chars=%d entities=%d",
            len(text),
            len(analyzer_results),
        )
        body = {
            "text": text,
            "analyzer_results": [entity.model_dump(mode="json") for entity in analyzer_results],
        }
        try:
            response = await self._http.post("/anonymize", json=body)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AnonymizerError(f"anonymizer failed: {exc}") from exc
        return AnonymizeResult.from_api_response(response.json())
