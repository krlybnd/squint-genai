from abc import ABC

from pydantic import BaseModel, ConfigDict, Field


class VectorPayload(BaseModel, ABC):
    """Abstract Qdrant point payload. Domain models inherit this; the client is generic over it."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    point_type: str | None = None
    tenant_id: str | None = None
    text: str | None = None
    doc_id: str | None = None
    source_file: str | None = None
    page: str | int | None = None
    page_label: str | int | None = None
    section: str | None = None
    node_content: str | None = Field(default=None, alias="_node_content")
