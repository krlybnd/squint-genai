"""Live Qdrant corpus checks for the eval suite."""

from __future__ import annotations

from qdrant_client import QdrantClient


def require_qdrant_collection(*, url: str, collection: str) -> list[str]:
    """Return existing collection names, or raise if ``collection`` is missing."""
    client = QdrantClient(url=url)
    try:
        names = [item.name for item in client.get_collections().collections]
    except Exception as exc:
        raise RuntimeError(f"Qdrant unreachable at {url}: {exc}") from exc
    if collection not in names:
        available = ", ".join(names) if names else "(none)"
        raise RuntimeError(
            f"Qdrant collection {collection!r} does not exist at {url}. "
            f"Available: {available}. Set EVAL_SUT_QDRANT_COLLECTION to the running "
            "stack's QDRANT_COLLECTION (repo-root .env), or re-index resources/ PDFs "
            "into this collection."
        )
    return names
