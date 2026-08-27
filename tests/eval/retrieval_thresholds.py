"""Default thresholds for live retrieval IR metrics (Tier 1)."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_EVAL_K = 5

# Applied to aggregate scores over non-abstention goldens against indexed resources/.
RECALL_AT_K_MIN = 0.75
PRECISION_AT_K_MIN = 0.45
HIT_RATE_AT_K_MIN = 0.75
MRR_MIN = 0.65
NDCG_AT_K_MIN = 0.65

# Abstention: fraction of no-corpus questions with zero relevant hits in top-k.
ABSTENTION_PRECISION_MIN = 0.8


@dataclass(frozen=True, slots=True)
class RetrievalThresholds:
    k: int = DEFAULT_EVAL_K
    recall_at_k_min: float = RECALL_AT_K_MIN
    precision_at_k_min: float = PRECISION_AT_K_MIN
    hit_rate_at_k_min: float = HIT_RATE_AT_K_MIN
    mrr_min: float = MRR_MIN
    ndcg_at_k_min: float = NDCG_AT_K_MIN
    abstention_precision_min: float = ABSTENTION_PRECISION_MIN
