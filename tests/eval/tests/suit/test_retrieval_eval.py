"""Tier 1 live gate: retrieval IR against indexed `resources/` PDFs."""

from agentic_eval.modules.retrieval.experiment import RetrievalExperiment
from suit.settings import SuitSettings


def test_retrieval_ir_aggregate_meets_thresholds(suit: SuitSettings) -> None:
    """Labeled goldens must retrieve the expected source file from the live stack.

    Corpus: ``suit.golden.known_source_files`` (Transformer, RAG, Constitution, NASA, NIST).
    Metrics: Recall@k, Precision@k, Hit Rate@k, MRR, nDCG@k — no judge LLM.
    Gate: ``suit.retrieval`` (``EVAL_RETRIEVAL_*``).
    """
    # Arrange
    experiment = RetrievalExperiment()
    gate = suit.retrieval

    # Act
    report = experiment.run(suit, suit.sut)
    report.print()

    # Assert
    averages = experiment.assert_gate(report, suit)
    print(
        f"  retrieval k={gate.k}: "
        f"recall={averages.recall_at_k:.2f}>={gate.minimums.recall_at_k:.2f} "
        f"prec={averages.precision_at_k:.2f}>={gate.minimums.precision_at_k:.2f} "
        f"hit={averages.hit_rate_at_k:.2f}>={gate.minimums.hit_rate_at_k:.2f} "
        f"mrr={averages.mrr:.2f}>={gate.minimums.mrr:.2f} "
        f"ndcg={averages.ndcg_at_k:.2f}>={gate.minimums.ndcg_at_k:.2f}"
    )
