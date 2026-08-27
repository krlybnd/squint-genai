from __future__ import annotations

from pydantic import BaseModel, Field


class GenerationResult(BaseModel):
    answer: str
    contexts: list[str] = Field(default_factory=list)
