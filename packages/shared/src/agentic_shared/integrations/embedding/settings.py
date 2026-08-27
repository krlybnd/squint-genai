from agentic_shared.core.resources.settings import ResourceSettings


class EmbeddingSettings(ResourceSettings):
    title: str = "embedding"
    embedding_model: str = "embed"
