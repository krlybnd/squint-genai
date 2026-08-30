from pydantic import Field

from agentic_shared.integrations.core.settings import IntegrationSettings
from agentic_shared.integrations.litellm.core.settings import LiteLLMSettings


class ChatSettings(IntegrationSettings):
    """Provider-agnostic chat settings. Instantiable with defaults alone."""

    title: str = Field(
        default="chat",
        description="Generic chat settings title; concrete providers override.",
    )


class LiteLLMChatSettings(LiteLLMSettings):
    """Chat via LiteLLM proxy. Model fields are proxy *aliases*.

    See ``operations/litellm/litellm.config.yaml``: ``generate`` / ``router`` /
    ``judge`` map to provider models behind the proxy.
    """

    title: str = Field(
        default="litellm-chat",
        description="Readiness/log label for the LiteLLM chat client.",
    )
    litellm_model: str = Field(
        default="generate",
        description="Default LiteLLM model alias for answer generation.",
    )
    litellm_router_model: str = Field(
        default="router",
        description="LiteLLM model alias for routing / classification style calls.",
    )
    litellm_judge_model: str = Field(
        default="judge",
        description="LiteLLM model alias for evaluation / judge calls.",
    )
