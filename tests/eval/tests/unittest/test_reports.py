from datetime import UTC, datetime
from pathlib import Path

from pydantic_evals import Case, Dataset

from agentic_eval.core.reports import (
    EVAL_REPORTS_DIR,
    append_abstention_section,
    format_deepeval_stamp,
    promote_deepeval_report,
    write_retrieval_report,
)
from agentic_eval.modules.retrieval.evaluators import RetrievalIR
from agentic_eval.modules.retrieval.metrics import RetrievalScores
from agentic_eval.modules.retrieval.settings import RetrievalSettings
from agentic_eval.settings import EVAL_ROOT


def test_eval_reports_dir_is_repo_reports_eval() -> None:
    # Assert
    assert EVAL_REPORTS_DIR == EVAL_ROOT.parents[1] / "reports" / "eval"
    assert EVAL_REPORTS_DIR.name == "eval"


def test_format_deepeval_stamp() -> None:
    # Assert
    assert format_deepeval_stamp("20260827_210105") == "2026-08-27 21:01:05"


def test_promote_deepeval_report_copies_timestamp_into_stable_file(tmp_path: Path) -> None:
    # Arrange
    stamped = tmp_path / "generation_20260827_210105.md"
    stamped.write_text("# 🚀 DeepEval Evaluation Results\n", encoding="utf-8")
    dest = tmp_path / "generation.md"

    # Act
    promote_deepeval_report(tmp_path, stem="generation", dest=dest)

    # Assert
    text = dest.read_text(encoding="utf-8")
    assert text.startswith("_Run: 2026-08-27 21:01:05_\n")
    assert "DeepEval Evaluation Results" in text


def test_write_retrieval_report_includes_run_time_and_scores(tmp_path: Path) -> None:
    # Arrange
    dataset = Dataset(
        name="retrieval_ir_stub",
        cases=[Case(name="hit", inputs="q1", expected_output="a.pdf")],
        evaluators=[RetrievalIR(k=1)],
    )
    report = dataset.evaluate_sync(lambda _: ["a.pdf"], progress=False, max_concurrency=1)
    dest = tmp_path / "retrieval.md"
    run_at = datetime(2026, 8, 27, 21, 1, 5, tzinfo=UTC)
    scores = RetrievalScores(
        recall_at_k=1.0,
        precision_at_k=1.0,
        hit_rate_at_k=1.0,
        mrr=1.0,
        ndcg_at_k=1.0,
    )
    gate = RetrievalSettings(k=1, minimums=scores)

    # Act
    write_retrieval_report(report, scores, gate, dest, run_at=run_at)

    # Assert
    text = dest.read_text(encoding="utf-8")
    assert "_Run: 2026-08-27 21:01:05 +0000_" in text
    assert "| MRR | 1.00 | 1.00 |" in text
    assert "q1" in text


def test_append_abstention_section(tmp_path: Path) -> None:
    # Arrange
    dest = tmp_path / "generation.md"
    dest.write_text("# gen\n", encoding="utf-8")

    # Act
    append_abstention_section(dest, total=2, failed=["unknown doc?"])

    # Assert
    text = dest.read_text(encoding="utf-8")
    assert "1/2 refused as expected." in text
    assert "unknown doc?" in text
