from pydantic import Field

from agentic_shared.infrastructure.core.settings import InfraSettings


class QdrantSettings(InfraSettings):
    """Qdrant vector store for hybrid dense + sparse retrieval."""

    title: str = Field(default="qdrant", description="Readiness/log label for the Qdrant client.")
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Base URL of the Qdrant HTTP API.",
    )
    qdrant_collection: str = Field(
        default="agentic_rag_eval_hybrid",
        description="Collection name holding chunk points for this deployment.",
    )
    dense_vector_name: str = Field(
        default="dense",
        description="Named dense vector field inside the collection.",
    )
    sparse_vector_name: str = Field(
        default="sparse",
        description="Named sparse vector field inside the collection.",
    )
    sparse_model: str = Field(
        default="Qdrant/bm25",
        description="FastEmbed / Qdrant sparse model id used at query and index time.",
    )
    top_k: int = Field(
        default=5,
        description="Default number of chunks returned after retrieval.",
    )
    candidate_top_k: int = Field(
        default=30,
        description="Candidate pool size before final top_k cut (hybrid search).",
    )
