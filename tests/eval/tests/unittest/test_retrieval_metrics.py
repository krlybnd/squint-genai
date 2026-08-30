from dataclasses import replace

from agentic_eval.modules.retrieval.metrics import (
    RetrievalEvalCase,
    aggregate_scores,
    dcg_at_k,
    ndcg_at_k,
    precision_at_k,
    reciprocal_rank,
    score_retrieval,
)


def test_recall_at_k_finds_relevant_in_top_k() -> None:
    # Arrange
    case = RetrievalEvalCase(
        query="q",
        expected_source_file="a.pdf",
        ranked_source_files=["b.pdf", "c.pdf", "a.pdf"],
        k=2,
    )

    # Act / Assert
    assert score_retrieval(case).recall_at_k == 0.0
    assert score_retrieval(replace(case, k=3)).recall_at_k == 1.0


def test_mrr_uses_first_relevant_rank() -> None:
    # Assert
    assert reciprocal_rank([0, 1, 0]) == 0.5


def test_precision_at_k_averages_relevant_in_window() -> None:
    # Assert
    assert precision_at_k([1, 0, 1, 0, 0], k=5) == 0.4


def test_ndcg_at_k_rewards_early_hits() -> None:
    # Assert
    assert ndcg_at_k([1, 0, 0], k=3) > ndcg_at_k([0, 0, 1], k=3)


def test_dcg_at_k_zero_when_no_relevant() -> None:
    # Assert
    assert dcg_at_k([0, 0, 0], k=3) == 0.0


def test_stem_match_accepts_pdf_when_golden_expects_md() -> None:
    case = RetrievalEvalCase(
        query="q",
        expected_source_file="investigation-dossier-alpha.md",
        ranked_source_files=["investigation-dossier-beta.pdf", "investigation-dossier-alpha.pdf"],
        k=5,
        stem_match=True,
    )
    assert score_retrieval(case).recall_at_k == 1.0
    assert score_retrieval(replace(case, stem_match=False)).recall_at_k == 0.0


def test_aggregate_scores_averages_cases() -> None:
    # Arrange
    first = score_retrieval(RetrievalEvalCase("q1", "a.pdf", ["a.pdf"], k=1))
    second = score_retrieval(RetrievalEvalCase("q2", "b.pdf", ["x.pdf"], k=1))

    # Act
    aggregate = aggregate_scores([first, second])

    # Assert
    assert aggregate.recall_at_k == 0.5
    assert aggregate.mrr == 0.5


def test_recall_at_k_empty_ranking() -> None:
    # Arrange
    scores = score_retrieval(RetrievalEvalCase("q", "a.pdf", [], k=5))

    # Assert
    assert scores.recall_at_k == 0.0
    assert scores.mrr == 0.0
