from openai import OpenAI

from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings


def _openai_client(llm: LLMSettings) -> OpenAI:
    return OpenAI(
        base_url=f"{llm.litellm_base_url.rstrip('/')}/v1",
        api_key=llm.proxy_api_key,
    )


def embed_dense_texts(
    texts: list[str],
    *,
    llm: LLMSettings,
    embedding: EmbeddingSettings,
) -> list[list[float]]:
    if not texts:
        return []
    response = _openai_client(llm).embeddings.create(
        model=embedding.embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


def embed_dense_text(text: str, *, llm: LLMSettings, embedding: EmbeddingSettings) -> list[float]:
    return embed_dense_texts([text], llm=llm, embedding=embedding)[0]
