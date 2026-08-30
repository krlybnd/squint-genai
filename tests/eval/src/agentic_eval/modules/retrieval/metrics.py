"""Deterministic information-retrieval metrics for ranked chunk lists."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict


def source_file_matches(expected: str, actual: str, *, stem_match: bool = False) -> bool:
    if expected == actual:
        return True
    if not stem_match:
        return False
    return Path(expected).stem == Path(actual).stem


@dataclass(frozen=True, slots=True)
class RetrievalEvalCase:
    query: str
    expected_source_file: str
    ranked_source_files: list[str]
    k: int = 5
    stem_match: bool = False


class RetrievalScores(BaseModel):
    model_config = ConfigDict(frozen=True)

    recall_at_k: float
    precision_at_k: float
    hit_rate_at_k: float
    mrr: float
    ndcg_at_k: float

    def assert_at_least(self, minimums: RetrievalScores) -> None:
        missed = {
            name: {"actual": actual, "min": getattr(minimums, name)}
            for name, actual in self.model_dump().items()
            if actual < getattr(minimums, name)
        }
        assert not missed, missed


DEFAULT_RETRIEVAL_MINIMUMS = RetrievalScores(
    recall_at_k=0.75,
    precision_at_k=0.45,
    hit_rate_at_k=0.75,
    mrr=0.65,
    ndcg_at_k=0.65,
)


def recall_at_k(relevances: list[int], *, k: int) -> float:
    if not relevances:
        return 0.0
    return 1.0 if any(relevances[:k]) else 0.0


def precision_at_k(relevances: list[int], *, k: int) -> float:
    if k <= 0:
        return 0.0
    return sum(relevances[:k]) / k


def hit_rate_at_k(relevances: list[int], *, k: int) -> float:
    return recall_at_k(relevances, k=k)


def reciprocal_rank(relevances: list[int]) -> float:
    for index, rel in enumerate(relevances, start=1):
        if rel:
            return 1.0 / index
    return 0.0


def dcg_at_k(relevances: list[int], *, k: int) -> float:
    score = 0.0
    for index, rel in enumerate(relevances[:k], start=1):
        if rel:
            score += 1.0 / math.log2(index + 1)
    return score


def ndcg_at_k(relevances: list[int], *, k: int) -> float:
    ideal = sorted(relevances, reverse=True)
    ideal_dcg = dcg_at_k(ideal, k=k)
    if ideal_dcg == 0.0:
        return 0.0
    return dcg_at_k(relevances, k=k) / ideal_dcg


def score_retrieval(case: RetrievalEvalCase) -> RetrievalScores:
    relevances = [
        1
        if source_file_matches(case.expected_source_file, source, stem_match=case.stem_match)
        else 0
        for source in case.ranked_source_files
    ]
    k = case.k
    return RetrievalScores(
        recall_at_k=recall_at_k(relevances, k=k),
        precision_at_k=precision_at_k(relevances, k=k),
        hit_rate_at_k=hit_rate_at_k(relevances, k=k),
        mrr=reciprocal_rank(relevances),
        ndcg_at_k=ndcg_at_k(relevances, k=k),
    )


def aggregate_scores(scores: list[RetrievalScores]) -> RetrievalScores:
    if not scores:
        return RetrievalScores(
            recall_at_k=0.0,
            precision_at_k=0.0,
            hit_rate_at_k=0.0,
            mrr=0.0,
            ndcg_at_k=0.0,
        )
    count = len(scores)
    return RetrievalScores(
        recall_at_k=sum(item.recall_at_k for item in scores) / count,
        precision_at_k=sum(item.precision_at_k for item in scores) / count,
        hit_rate_at_k=sum(item.hit_rate_at_k for item in scores) / count,
        mrr=sum(item.mrr for item in scores) / count,
        ndcg_at_k=sum(item.ndcg_at_k for item in scores) / count,
    )
