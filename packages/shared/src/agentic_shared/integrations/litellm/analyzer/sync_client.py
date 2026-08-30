from __future__ import annotations

from collections.abc import Sequence

import httpx

from agentic_shared.integrations.core.client import IntegrationClient
from agentic_shared.integrations.litellm.analyzer.errors import AnalyzerError
from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity
from agentic_shared.integrations.litellm.analyzer.settings import AnalyzerSettings


class AnalyzerSyncClient(IntegrationClient[AnalyzerSettings]):
    """Synchronous Presidio analyzer client for Celery indexing workers."""

    def __init__(self, settings: AnalyzerSettings) -> None:
        super().__init__(settings)
        self._http = httpx.Client(
            base_url=settings.analyzer_api_base.rstrip("/"),
            timeout=httpx.Timeout(60.0, connect=5.0),
        )

    def is_healthy(self) -> bool:
        try:
            response = self._http.get("/health")
            return response.status_code == 200
        except httpx.HTTPError:
            self._logger.debug("%s health check failed", self.title, exc_info=True)
            return False

    def close(self) -> None:
        try:
            self._http.close()
        finally:
            super().close()

    def analyze(self, text: str, *, language: str = "en") -> list[AnalyzerEntity]:
        self._logger.info("analyze sync chars=%d language=%s", len(text), language)
        try:
            response = self._http.post("/analyze", json={"text": text, "language": language})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AnalyzerError(f"analyzer failed: {exc}") from exc
        payload: Sequence[dict] = response.json()
        return [AnalyzerEntity.model_validate(item) for item in payload]


__all__ = ["AnalyzerSyncClient"]
