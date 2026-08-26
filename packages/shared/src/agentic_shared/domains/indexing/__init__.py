"""Indexing domain models (Celery task results, worker outcomes)."""

from agentic_shared.domains.indexing.models import IndexDocumentTaskResult

__all__ = ["IndexDocumentTaskResult"]
