from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field


class RerankHit(BaseModel):
    """One document score from LiteLLM `/rerank` (or raw TEI)."""

    model_config = ConfigDict(extra="ignore")

    index: int
    score: float


class RerankResult(BaseModel):
    """Normalized rerank hits, highest score first."""

    model_config = ConfigDict(extra="ignore")

    hits: list[RerankHit] = Field(default_factory=list)

    @classmethod
    def from_api_response(cls, data: Any) -> Self:
        items: list[Any]
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            raw = data.get("results")
            if raw is None:
                raw = data.get("data")
            items = raw if isinstance(raw, list) else []
        else:
            items = []

        hits: list[RerankHit] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            index = item.get("index")
            score = item.get("relevance_score", item.get("score"))
            if index is None or score is None:
                continue
            hits.append(RerankHit(index=int(index), score=float(score)))
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return cls(hits=hits)
