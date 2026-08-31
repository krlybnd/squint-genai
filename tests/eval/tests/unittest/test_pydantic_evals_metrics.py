from pydantic_evals.evaluators import EvaluatorContext
from pydantic_evals.otel._errors import SpanTreeRecordingError

from agentic_eval.core.pydantic_evals.metrics import RetrievalIR, stem_match


def _ctx(*, expected: list[str], ranked: list[str]) -> EvaluatorContext[str, list[str]]:
    return EvaluatorContext(
        name="case",
        inputs="question",
        metadata=None,
        expected_output=expected,
        output=ranked,
        duration=0.0,
        _span_tree=SpanTreeRecordingError("unittest"),
        attributes={},
        metrics={},
    )


def test_stem_match_equates_md_and_pdf() -> None:
    # Arrange / Act / Assert
    assert stem_match("investigation-dossier-alpha.md", "investigation-dossier-alpha.pdf")
    assert not stem_match("investigation-dossier-alpha.md", "investigation-dossier-beta.md")


def test_retrieval_ir_hit_recall_precision_on_ranked_sources() -> None:
    # Arrange
    metric = RetrievalIR(k=5)
    ctx = _ctx(
        expected=["investigation-dossier-alpha.md", "investigation-dossier-beta.md"],
        ranked=[
            "investigation-dossier-alpha.pdf",
            "investigation-dossier-gamma-decoy.md",
            "investigation-dossier-beta.md",
            "other.md",
            "noise.md",
        ],
    )

    # Act
    scores = metric.evaluate(ctx)

    # Assert
    assert scores["hit_rate_at_k"] == 1.0
    assert scores["document_recall_at_k"] == 1.0
    assert scores["chunk_precision_at_k"] == 0.4
    assert scores["mrr"] == 1.0


def test_retrieval_ir_miss_when_relevant_set_absent() -> None:
    # Arrange
    metric = RetrievalIR(k=5)
    ctx = _ctx(
        expected=["investigation-dossier-alpha.md"],
        ranked=["gamma.md", "other.md", "noise.md", "x.md", "y.md"],
    )

    # Act
    scores = metric.evaluate(ctx)

    # Assert
    assert scores["hit_rate_at_k"] == 0.0
    assert scores["document_recall_at_k"] == 0.0
    assert scores["mrr"] == 0.0
    assert scores["ndcg_at_k"] == 0.0
