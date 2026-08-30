from pydantic import Field

from agentic_shared.core.settings.secrets import SecuredStr
from agentic_shared.integrations.core.settings import IntegrationSettings


class LiteLLMSettings(IntegrationSettings):
    """Shared LiteLLM proxy connection settings (base URL + master key)."""

    title: str = Field(
        default="litellm",
        description="Readiness/log label for the LiteLLM proxy connection.",
    )
    litellm_base_url: str = Field(
        default="http://localhost:4000",
        description="LiteLLM proxy base URL (without trailing /v1; clients append it).",
    )
    litellm_master_key: SecuredStr = Field(
        default=SecuredStr("sk-change-me"),
        description=("Bearer token apps send to LiteLLM. Must match the proxy LITELLM_MASTER_KEY."),
    )

    @property
    def proxy_api_key(self) -> str:
        return self.litellm_master_key.get_secret_value()
