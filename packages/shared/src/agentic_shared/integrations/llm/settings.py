from agentic_shared.core.resources.settings import ResourceSettings


class LLMSettings(ResourceSettings):
    """LiteLLM proxy. Model fields are proxy *aliases*, not provider ids.

    See ``operations/litellm/litellm.config.yaml``: ``generate`` / ``router`` /
    ``judge`` map to OpenAI models behind the proxy.
    """

    title: str = "litellm"
    litellm_base_url: str = "http://localhost:4000"
    litellm_model: str = "generate"
    litellm_router_model: str = "router"
    litellm_judge_model: str = "judge"
    openai_api_key: str = "sk-change-me"
    # Bearer token for app -> LiteLLM proxy auth (defaults to openai_api_key)
    litellm_master_key: str = ""

    @property
    def proxy_api_key(self) -> str:
        return self.litellm_master_key or self.openai_api_key
