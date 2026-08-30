from pydantic import Field

from agentic_shared.integrations.core.settings import IntegrationSettings


class AnonymizerSettings(IntegrationSettings):
    """Anonymizer sidecar (compose profile ``guardrails`` / Presidio anonymizer)."""

    title: str = Field(
        default="anonymizer",
        description="Readiness/log label for the anonymizer client.",
    )
    anonymizer_api_base: str = Field(
        default="http://localhost:5001",
        description="Anonymizer base URL (host or docker DNS). Env: ANONYMIZER_API_BASE.",
    )
