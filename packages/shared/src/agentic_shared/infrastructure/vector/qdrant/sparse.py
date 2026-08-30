from __future__ import annotations

from functools import lru_cache

from fastembed import SparseTextEmbedding
from qdrant_client.http.models import SparseVector


@lru_cache
def _sparse_model(model_name: str) -> SparseTextEmbedding:
    return SparseTextEmbedding(model_name=model_name)


def embed_sparse_texts(texts: list[str], *, model_name: str) -> list[SparseVector]:
    if not texts:
        return []
    model = _sparse_model(model_name)
    return [
        SparseVector(indices=embedding.indices.tolist(), values=embedding.values.tolist())
        for embedding in model.embed(texts)
    ]


def embed_sparse_text(text: str, *, model_name: str) -> SparseVector:
    return embed_sparse_texts([text], model_name=model_name)[0]
