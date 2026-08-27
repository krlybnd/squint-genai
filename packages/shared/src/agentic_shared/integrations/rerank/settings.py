from pydantic import model_validator

from agentic_shared.core.resources.settings import ResourceSettings


class RerankSettings(ResourceSettings):
    title: str = "rerank"
    rerank_model: str = "rerank"
    rerank_enabled: bool = False
    cohere_api_key: str = ""

    @model_validator(mode="after")
    def _disable_without_cohere_key(self) -> "RerankSettings":
        if self.rerank_enabled and not self.cohere_api_key.strip():
            self.rerank_enabled = False
        return self
