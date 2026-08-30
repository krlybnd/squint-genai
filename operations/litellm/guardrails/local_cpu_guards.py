"""LiteLLM custom guardrail: Presidio PII mask + llm-guard PromptInjection."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Literal

from litellm.integrations.custom_guardrail import CustomGuardrail
from litellm.llms.custom_httpx.http_handler import (
    get_async_httpx_client,
    httpxSpecialProvider,
)
from litellm.types.guardrails import GuardrailEventHooks
from litellm.types.utils import GenericGuardrailAPIInputs

if TYPE_CHECKING:
    from litellm.litellm_core_utils.litellm_logging import Logging as LiteLLMLoggingObj

# Model aliases that always run this guardrail (LiteLLM model_list.guardrails
# merge often races pre_call before model_id is set — pin by alias name).
GUARDED_MODEL_ALIASES = frozenset({"generate-guarded", "router-guarded"})


class LocalCpuGuardrails(CustomGuardrail):
    """
    Single guardrail for generate-guarded / router-guarded:
    1) Mask PII via Presidio analyzer + anonymizer
    2) Block prompt injection via llm-guard-api
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.llm_guard_key = api_key or os.getenv("LLM_GUARD_AUTH_TOKEN", "poc-local-classifier")
        self.llm_guard_base = (
            api_base or os.getenv("LLM_GUARD_API_BASE", "http://llm-guard:8000")
        ).rstrip("/")
        self.analyzer_base = os.getenv(
            "PRESIDIO_ANALYZER_API_BASE", "http://presidio-analyzer:3000"
        ).rstrip("/")
        self.anonymizer_base = os.getenv(
            "PRESIDIO_ANONYMIZER_API_BASE", "http://presidio-anonymizer:3000"
        ).rstrip("/")
        super().__init__(**kwargs)

    def should_run_guardrail(self, data: dict, event_type: GuardrailEventHooks) -> bool:
        model = str(data.get("model") or "")
        if model in GUARDED_MODEL_ALIASES and self._event_hook_is_event_type(event_type):
            return True
        return super().should_run_guardrail(data=data, event_type=event_type)

    async def apply_guardrail(
        self,
        inputs: GenericGuardrailAPIInputs,
        request_data: dict,
        input_type: Literal["request", "response"],
        logging_obj: LiteLLMLoggingObj | None = None,
    ) -> GenericGuardrailAPIInputs:
        if input_type != "request":
            return inputs

        client = get_async_httpx_client(llm_provider=httpxSpecialProvider.LoggingCallback)
        texts = list(inputs.get("texts") or [])
        masked: list[str] = []
        for text in texts:
            if not (text or "").strip():
                masked.append(text)
                continue
            # Injection on original text first — Presidio placeholders like
            # <EMAIL_ADDRESS> false-positive the DeBERTa scanner.
            if not await self._is_valid_prompt(client, text):
                raise Exception("Violated guardrail policy: prompt injection")
            masked.append(await self._mask_pii(client, text))
        inputs["texts"] = masked
        return inputs

    async def _mask_pii(self, client: Any, text: str) -> str:
        analyze = await client.post(
            f"{self.analyzer_base}/analyze",
            headers={"Content-Type": "application/json"},
            json={"text": text, "language": "en"},
            timeout=60.0,
        )
        analyze.raise_for_status()
        entities = analyze.json()
        if not entities:
            return text
        anon = await client.post(
            f"{self.anonymizer_base}/anonymize",
            headers={"Content-Type": "application/json"},
            json={"text": text, "analyzer_results": entities},
            timeout=60.0,
        )
        anon.raise_for_status()
        data = anon.json()
        return data.get("text") or text

    async def _is_valid_prompt(self, client: Any, prompt: str) -> bool:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llm_guard_key}",
        }
        for path in ("/analyze/prompt", "/scan/prompt"):
            response = await client.post(
                f"{self.llm_guard_base}{path}",
                headers=headers,
                json={"prompt": prompt},
                timeout=60.0,
            )
            if response.status_code == 404:
                continue
            response.raise_for_status()
            return bool(response.json().get("is_valid", True))
        raise Exception("llm-guard analyze/scan endpoint not found")
