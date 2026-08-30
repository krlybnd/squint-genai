"""LiteLLM custom guardrail → llm-guard-api PromptInjection scanner."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Literal

from litellm.integrations.custom_guardrail import CustomGuardrail
from litellm.llms.custom_httpx.http_handler import (
    get_async_httpx_client,
    httpxSpecialProvider,
)
from litellm.types.utils import GenericGuardrailAPIInputs

if TYPE_CHECKING:
    from litellm.litellm_core_utils.litellm_logging import Logging as LiteLLMLoggingObj


class PromptInjectionGuardrail(CustomGuardrail):
    """Block prompts that llm-guard marks is_valid=false."""

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        **kwargs,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_GUARD_AUTH_TOKEN", "poc-local-classifier")
        self.api_base = (
            api_base or os.getenv("LLM_GUARD_API_BASE", "http://llm-guard:8000")
        ).rstrip("/")
        super().__init__(**kwargs)

    async def apply_guardrail(
        self,
        inputs: GenericGuardrailAPIInputs,
        request_data: dict,
        input_type: Literal["request", "response"],
        logging_obj: LiteLLMLoggingObj | None = None,
    ) -> GenericGuardrailAPIInputs:
        if input_type != "request":
            return inputs

        texts = list(inputs.get("texts") or [])
        for text in texts:
            if not (text or "").strip():
                continue
            if not await self._is_valid_prompt(text):
                raise Exception("Violated guardrail policy: prompt injection")
        return inputs

    async def _is_valid_prompt(self, prompt: str) -> bool:
        client = get_async_httpx_client(llm_provider=httpxSpecialProvider.LoggingCallback)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        # Prefer /analyze/prompt; fall back to /scan/prompt (older images).
        for path in ("/analyze/prompt", "/scan/prompt"):
            response = await client.post(
                f"{self.api_base}{path}",
                headers=headers,
                json={"prompt": prompt},
                timeout=60.0,
            )
            if response.status_code == 404:
                continue
            response.raise_for_status()
            data = response.json()
            return bool(data.get("is_valid", True))
        raise Exception("llm-guard analyze/scan endpoint not found")
