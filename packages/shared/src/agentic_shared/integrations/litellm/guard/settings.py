from pydantic import Field

from agentic_shared.core.settings.secrets import SecuredStr
from agentic_shared.integrations.core.settings import IntegrationSettings


class GuardSettings(IntegrationSettings):
    """Guard sidecar (compose profile ``guardrails`` / llm-guard-api)."""

    title: str = Field(
        default="guard",
        description="Readiness/log label for the guard client.",
    )
    guard_api_base: str = Field(
        default="http://localhost:8010",
        description=(
            "Guard base URL (host :8010 or docker DNS llm-guard:8000). Env: GUARD_API_BASE."
        ),
    )
    guard_auth_token: SecuredStr = Field(
        default=SecuredStr("poc-local-classifier"),
        description="Bearer token for the guard API. Env: GUARD_AUTH_TOKEN.",
    )

    @property
    def bearer_token(self) -> str:
        return self.guard_auth_token.get_secret_value()
