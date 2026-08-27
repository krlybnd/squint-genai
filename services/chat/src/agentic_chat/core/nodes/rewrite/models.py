from pydantic import BaseModel, ConfigDict


class RewriteRouterResponse(BaseModel):
    """Adaptive RAG gate: retrieve vs converse. Search uses the original user query."""

    model_config = ConfigDict(extra="ignore")

    needs_document_search: bool = True
    reason: str = ""
    search_query: str = ""

    @property
    def rewrite_reason(self) -> str:
        return self.reason
