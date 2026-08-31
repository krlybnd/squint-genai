from __future__ import annotations

import httpx

from agentic_shared.integrations.core.client import IntegrationClient
from agentic_shared.integrations.litellm.analyzer.errors import AnalyzerError
from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity
from agentic_shared.integrations.litellm.analyzer.settings import AnalyzerSettings


class AnalyzerClient(IntegrationClient[AnalyzerSettings]):
    """Analyzer HTTP client (PII detect)."""

    def __init__(self, settings: AnalyzerSettings) -> None:
        super().__init__(settings)
        self._http = httpx.AsyncClient(
            base_url=settings.analyzer_api_base.rstrip("/"),
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

    async def analyze(self, text: str, *, language: str = "en") -> list[AnalyzerEntity]:
        self._logger.info("analyze language=%s chars=%d", language, len(text))
        try:
            response = await self._http.post(
                "/analyze",
                json=self._settings.analyze_payload(text, language=language),
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AnalyzerError(f"analyzer failed: {exc}") from exc
        payload = response.json()
        if not isinstance(payload, list):
            raise AnalyzerError("analyzer returned non-list JSON")
        return [AnalyzerEntity.model_validate(item) for item in payload]
