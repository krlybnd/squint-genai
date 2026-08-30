from agentic_shared.core.resources.client import BaseResourceClient
from agentic_shared.integrations.core.settings import IntegrationSettings


class IntegrationClient[S: IntegrationSettings](BaseResourceClient[S]):
    """Base client for third-party API integrations (LLM, embedding, IdP, …)."""


__all__ = ["IntegrationClient"]
