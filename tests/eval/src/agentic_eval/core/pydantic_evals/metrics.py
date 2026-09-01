"""IR metrics as pydantic-evals ``Evaluator`` extensions (not built into the SDK)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


def stem_match(expected: str, actual: str) -> bool:
    return expected == actual or Path(expected).stem == Path(actual).stem


def _dcg(relevances: list[int], k: int) -> float:
    return sum(1.0 / math.log2(i + 1) for i, rel in enumerate(relevances[:k], start=1) if rel)


@dataclass
class RetrievalIR(Evaluator[str, list[str]]):
    """Document Recall@k, chunk Precision@k, Hit Rate@k, MRR, nDCG@k on ranked source files."""

    k: int = 5

    def evaluate(self, ctx: EvaluatorContext[str, list[str]]) -> dict[str, float]:
        expected = [str(item) for item in ctx.expected_output] if ctx.expected_output else []
        ranked = ctx.output
        k = self.k
        rel = [1 if any(stem_match(exp, src) for exp in expected) else 0 for src in ranked]
        found: set[str] = set()
        for src in ranked[:k]:
            for exp in expected:
                if exp not in found and stem_match(exp, src):
                    found.add(exp)
        recall = (len(found) / len(expected)) if expected else 0.0
        prec = (sum(rel[:k]) / k) if k else 0.0
        hit = 1.0 if any(rel[:k]) else 0.0
        mrr = next((1.0 / i for i, bit in enumerate(rel, start=1) if bit), 0.0)
        ideal = _dcg(sorted(rel, reverse=True), k)
        ndcg = (_dcg(rel, k) / ideal) if ideal else 0.0
        return {
            "document_recall_at_k": recall,
            "chunk_precision_at_k": prec,
            "hit_rate_at_k": hit,
            "mrr": mrr,
            "ndcg_at_k": ndcg,
        }
