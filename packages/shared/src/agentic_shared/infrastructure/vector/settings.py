from agentic_shared.infrastructure.core.settings import InfraSettings


class QdrantSettings(InfraSettings):
    title: str = "qdrant"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "agentic_rag_eval_hybrid"
    dense_vector_name: str = "dense"
    sparse_vector_name: str = "sparse"
    sparse_model: str = "Qdrant/bm25"
    top_k: int = 5
    candidate_top_k: int = 30
