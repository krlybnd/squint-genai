from openai import OpenAI

from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings


def _openai_client(llm: LiteLLMChatSettings) -> OpenAI:
    return OpenAI(
        base_url=f"{llm.litellm_base_url.rstrip('/')}/v1",
        api_key=llm.proxy_api_key,
    )


def embed_dense_texts(
    texts: list[str],
    *,
    llm: LiteLLMChatSettings,
    embedding: LiteLLMEmbeddingSettings,
) -> list[list[float]]:
    if not texts:
        return []
    response = _openai_client(llm).embeddings.create(
        model=embedding.embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


def embed_dense_text(
    text: str, *, llm: LiteLLMChatSettings, embedding: LiteLLMEmbeddingSettings
) -> list[float]:
    return embed_dense_texts([text], llm=llm, embedding=embedding)[0]
