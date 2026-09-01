"""Light shared live-eval settings. Every suite asks for the OpenAI-compatible key."""

from __future__ import annotations

from pathlib import Path

from agentic_shared.core.settings.base import EnvSettings
from agentic_shared.core.settings.secrets import SecuredStr
from pydantic import AliasChoices, Field
from pydantic_settings import SettingsConfigDict

# tests/eval/src/agentic_eval/core/settings.py → parents[3]=tests/eval
EVAL_ROOT = Path(__file__).resolve().parents[3]


def eval_env_file() -> Path | None:
    path = EVAL_ROOT / ".env"
    return path if path.is_file() else None


class CoreSettings(EnvSettings):
    """LiteLLM proxy, tenant, and published compose URLs for api/chat HTTP."""

    model_config = SettingsConfigDict(
        env_prefix="EVAL_",
        extra="ignore",
        env_file=None,
        populate_by_name=True,
        env_ignore_empty=True,
    )

    tenant_id: str = "default"
    max_concurrency: int = 20
    openai_base_url: str = Field(
        default="http://localhost:4000",
        validation_alias=AliasChoices(
            "EVAL_OPENAI_BASE_URL",
            "EVAL_SUT_LITELLM_BASE_URL",
        ),
    )
    openai_api_key: SecuredStr = Field(
        default=SecuredStr("sk-change-me"),
        validation_alias=AliasChoices(
            "EVAL_OPENAI_API_KEY",
            "EVAL_SUT_LITELLM_API_KEY",
            "LITELLM_MASTER_KEY",
            "OPENAI_API_KEY",
        ),
    )
    chat_url: str = Field(
        default="http://localhost:8002",
        validation_alias=AliasChoices("EVAL_CHAT_URL", "EVAL_SUT_CHAT_URL"),
    )
    api_url: str = Field(
        default="http://localhost:8000",
        validation_alias=AliasChoices("EVAL_API_URL", "EVAL_SUT_API_URL"),
    )
    api_key: SecuredStr = Field(
        default=SecuredStr(""),
        validation_alias=AliasChoices("EVAL_API_KEY", "EVAL_SUT_API_KEY", "API_KEY"),
    )
    internal_service_key: SecuredStr = Field(
        default=SecuredStr(""),
        validation_alias=AliasChoices(
            "EVAL_INTERNAL_SERVICE_KEY",
            "EVAL_SUT_INTERNAL_SERVICE_KEY",
            "INTERNAL_SERVICE_KEY",
        ),
    )

    def auth_headers(self) -> dict[str, str]:
        headers = {"X-Tenant-Id": self.tenant_id}
        api_key = self.api_key.get_secret_value().strip()
        if api_key:
            headers["X-API-Key"] = api_key
        internal = self.internal_service_key.get_secret_value().strip()
        if internal:
            headers["X-Internal-Service-Key"] = internal
        return headers

    @property
    def openai_compatible_base_url(self) -> str:
        return f"{self.openai_base_url.rstrip('/')}/v1"

    @property
    def proxy_api_key(self) -> str:
        return self.openai_api_key.get_secret_value()
