from agentic_shared.core.resources.settings import ResourceSettings


class LLMSettings(ResourceSettings):
    title: str = "litellm"
    litellm_base_url: str = "http://localhost:4000"
    litellm_model: str = "gpt-4o-mini"
    openai_api_key: str = "sk-change-me"
    # Bearer token for app -> LiteLLM proxy auth (defaults to openai_api_key)
    litellm_master_key: str = ""

    @property
    def proxy_api_key(self) -> str:
        return self.litellm_master_key or self.openai_api_key
