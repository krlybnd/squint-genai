from dataclasses import replace

from retrieval_metrics import (
    RetrievalEvalCase,
    aggregate_scores,
    dcg_at_k,
    ndcg_at_k,
    precision_at_k,
    reciprocal_rank,
    score_retrieval,
)


def test_recall_at_k_finds_relevant_in_top_k() -> None:
    case = RetrievalEvalCase(
        query="q",
        expected_source_file="a.pdf",
        ranked_source_files=["b.pdf", "c.pdf", "a.pdf"],
        k=2,
    )
    scores = score_retrieval(case)
    assert scores.recall_at_k == 0.0
    assert score_retrieval(replace(case, k=3)).recall_at_k == 1.0


def test_mrr_uses_first_relevant_rank() -> None:
    relevances = [0, 1, 0]
    assert reciprocal_rank(relevances) == 0.5


def test_precision_at_k_averages_relevant_in_window() -> None:
    relevances = [1, 0, 1, 0, 0]
    assert precision_at_k(relevances, k=5) == 0.4


def test_ndcg_at_k_rewards_early_hits() -> None:
    early = [1, 0, 0]
    late = [0, 0, 1]
    assert ndcg_at_k(early, k=3) > ndcg_at_k(late, k=3)


def test_dcg_at_k_zero_when_no_relevant() -> None:
    assert dcg_at_k([0, 0, 0], k=3) == 0.0


def test_aggregate_scores_averages_cases() -> None:
    first = score_retrieval(
        RetrievalEvalCase("q1", "a.pdf", ["a.pdf"], k=1),
    )
    second = score_retrieval(
        RetrievalEvalCase("q2", "b.pdf", ["x.pdf"], k=1),
    )
    aggregate = aggregate_scores([first, second])
    assert aggregate.recall_at_k == 0.5
    assert aggregate.mrr == 0.5


def test_recall_at_k_empty_ranking() -> None:
    case = RetrievalEvalCase("q", "a.pdf", [], k=5)
    scores = score_retrieval(case)
    assert scores.recall_at_k == 0.0
    assert scores.mrr == 0.0
