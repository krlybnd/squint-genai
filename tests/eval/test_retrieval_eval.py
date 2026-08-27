import asyncio
import os

import pytest

from goldens import load_goldens
from retrieval_app import retrieve_ranked_source_files
from retrieval_metrics import RetrievalEvalCase, aggregate_scores, score_retrieval
from retrieval_thresholds import RetrievalThresholds

pytestmark = [
    pytest.mark.eval,
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("EVAL_MODE") != "live",
        reason="Retrieval IR eval needs indexed resources/ corpus (make eval-live)",
    ),
]

RETRIEVAL_GOLDENS = [golden for golden in load_goldens() if not golden.expect_abstention]
THRESHOLDS = RetrievalThresholds()


def test_retrieval_ir_aggregate_meets_thresholds() -> None:
    cases = []
    for golden in RETRIEVAL_GOLDENS:
        ranked = asyncio.run(retrieve_ranked_source_files(golden.input, top_k=THRESHOLDS.k))
        cases.append(
            RetrievalEvalCase(
                query=golden.input,
                expected_source_file=golden.expected_source_file or "",
                ranked_source_files=ranked,
                k=THRESHOLDS.k,
            )
        )
    aggregate = aggregate_scores([score_retrieval(case) for case in cases])
    assert aggregate.recall_at_k >= THRESHOLDS.recall_at_k_min, aggregate
    assert aggregate.precision_at_k >= THRESHOLDS.precision_at_k_min, aggregate
    assert aggregate.hit_rate_at_k >= THRESHOLDS.hit_rate_at_k_min, aggregate
    assert aggregate.mrr >= THRESHOLDS.mrr_min, aggregate
    assert aggregate.ndcg_at_k >= THRESHOLDS.ndcg_at_k_min, aggregate
