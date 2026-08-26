from pydantic import BaseModel, ConfigDict


class RewriteRouterResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    needs_document_search: bool = False
    search_query: str = ""
    reason: str = ""

    @property
    def rewrite_reason(self) -> str:
        return self.reason
