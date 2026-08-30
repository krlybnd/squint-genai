from __future__ import annotations

import httpx

from agentic_shared.integrations.core.client import IntegrationClient
from agentic_shared.integrations.litellm.guard.errors import GuardError
from agentic_shared.integrations.litellm.guard.models import GuardResult
from agentic_shared.integrations.litellm.guard.settings import GuardSettings


class GuardClient(IntegrationClient[GuardSettings]):
    """Guard HTTP client (llm-guard-api BanSubstrings / PromptInjection / …)."""

    def __init__(self, settings: GuardSettings) -> None:
        super().__init__(settings)
        self._http = httpx.AsyncClient(
            base_url=settings.guard_api_base.rstrip("/"),
            timeout=httpx.Timeout(60.0, connect=5.0),
            headers={"Authorization": f"Bearer {settings.bearer_token}"},
        )

    async def health_check(self) -> bool:
        try:
            response = await self._http.get("/healthz")
            return response.status_code == 200
        except httpx.HTTPError:
            self._logger.debug("%s health check failed", self.title, exc_info=True)
            return False

    async def aclose(self) -> None:
        try:
            await self._http.aclose()
        finally:
            await super().aclose()

    async def analyze_prompt(self, prompt: str) -> GuardResult:
        self._logger.info("guard analyze_prompt chars=%d", len(prompt))
        last_error: Exception | None = None
        for path in ("/analyze/prompt", "/scan/prompt"):
            try:
                response = await self._http.post(path, json={"prompt": prompt})
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                return GuardResult.from_api_response(response.json())
            except httpx.HTTPError as exc:
                last_error = exc
                continue
        detail = f": {last_error}" if last_error is not None else ""
        raise GuardError(f"guard analyze/scan endpoint failed{detail}")
