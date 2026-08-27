from pydantic_evals import Case, Dataset

from agentic_eval.modules.retrieval.evaluators import RetrievalIR
from agentic_eval.modules.retrieval.experiment import assert_retrieval_gate
from agentic_eval.modules.retrieval.metrics import RetrievalScores
from agentic_eval.modules.retrieval.settings import RetrievalSettings


def test_retrieval_ir_experiment_averages_and_gate() -> None:
    # Arrange
    dataset = Dataset(
        name="retrieval_ir_stub",
        cases=[
            Case(name="hit", inputs="q1", expected_output="a.pdf"),
            Case(name="miss", inputs="q2", expected_output="b.pdf"),
        ],
        evaluators=[RetrievalIR(k=1)],
    )

    def retrieve(question: str) -> list[str]:
        return ["a.pdf"] if question == "q1" else ["x.pdf"]

    # Act
    report = dataset.evaluate_sync(retrieve, progress=False, max_concurrency=1)
    averages = report.averages()
    assert averages is not None

    # Assert
    assert averages.scores["recall_at_k"] == 0.5
    assert averages.scores["mrr"] == 0.5
    assert_retrieval_gate(
        report,
        RetrievalSettings(
            minimums=RetrievalScores(
                recall_at_k=0.5,
                precision_at_k=0.5,
                hit_rate_at_k=0.5,
                mrr=0.5,
                ndcg_at_k=0.5,
            ),
        ),
    )
