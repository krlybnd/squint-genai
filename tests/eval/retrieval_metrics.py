"""Deterministic information-retrieval metrics for ranked chunk lists."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievalEvalCase:
    query: str
    expected_source_file: str
    ranked_source_files: list[str]
    k: int = 5


@dataclass(frozen=True, slots=True)
class RetrievalMetricScores:
    recall_at_k: float
    precision_at_k: float
    hit_rate_at_k: float
    mrr: float
    ndcg_at_k: float


def is_relevant(source_file: str, expected_source_file: str) -> bool:
    return source_file == expected_source_file


def binary_relevances(ranked_source_files: list[str], expected_source_file: str) -> list[int]:
    return [
        1 if is_relevant(source_file, expected_source_file) else 0
        for source_file in ranked_source_files
    ]


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


def score_retrieval(case: RetrievalEvalCase) -> RetrievalMetricScores:
    relevances = binary_relevances(case.ranked_source_files, case.expected_source_file)
    k = case.k
    return RetrievalMetricScores(
        recall_at_k=recall_at_k(relevances, k=k),
        precision_at_k=precision_at_k(relevances, k=k),
        hit_rate_at_k=hit_rate_at_k(relevances, k=k),
        mrr=reciprocal_rank(relevances),
        ndcg_at_k=ndcg_at_k(relevances, k=k),
    )


def aggregate_scores(scores: list[RetrievalMetricScores]) -> RetrievalMetricScores:
    if not scores:
        return RetrievalMetricScores(0.0, 0.0, 0.0, 0.0, 0.0)
    count = len(scores)
    return RetrievalMetricScores(
        recall_at_k=sum(item.recall_at_k for item in scores) / count,
        precision_at_k=sum(item.precision_at_k for item in scores) / count,
        hit_rate_at_k=sum(item.hit_rate_at_k for item in scores) / count,
        mrr=sum(item.mrr for item in scores) / count,
        ndcg_at_k=sum(item.ndcg_at_k for item in scores) / count,
    )
