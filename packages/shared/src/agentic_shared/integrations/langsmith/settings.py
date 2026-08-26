from pydantic_settings import SettingsConfigDict

from agentic_shared.core.settings.base import EnvSettings


class LangSmithSettings(EnvSettings):
    model_config = SettingsConfigDict(env_prefix="LANGSMITH_", env_file=".env", extra="ignore")

    enabled: bool = False
    api_key: str = ""
    project: str = "agentic-rag-eval"
    endpoint: str = "https://api.smith.langchain.com"
