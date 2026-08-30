from typing import Any

from pydantic import BaseModel, ConfigDict


class AnalyzerEntity(BaseModel):
    """One analyzer hit (Presidio-compatible JSON)."""

    model_config = ConfigDict(extra="allow")

    entity_type: str
    start: int
    end: int
    score: float = 0.0
    analysis_explanation: Any | None = None
