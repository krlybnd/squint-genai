"""Committed live-eval snapshots under ``reports/eval/`` (not gitignored ``.reports/``)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic_evals.reporting import EvaluationReport

from agentic_eval.modules.retrieval.metrics import RetrievalScores
from agentic_eval.modules.retrieval.settings import RetrievalSettings
from agentic_eval.settings import EVAL_ROOT

EVAL_REPORTS_DIR = EVAL_ROOT.parents[1] / "reports" / "eval"
GENERATION_REPORT = EVAL_REPORTS_DIR / "generation.md"
RETRIEVAL_REPORT = EVAL_REPORTS_DIR / "retrieval.md"


def format_deepeval_stamp(stamp: str) -> str:
    """Turn DeepEval's ``YYYYMMDD_HHMMSS`` filename stamp into a readable time."""
    parsed = datetime.strptime(stamp, "%Y%m%d_%H%M%S")
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def promote_deepeval_report(directory: Path, *, stem: str, dest: Path) -> Path:
    """Copy DeepEval's timestamped markdown to a stable README path.

    DeepEval writes ``{stem}_{YYYYMMDD_HHMMSS}.md`` (local time in the filename).
    """
    stamped = sorted(path for path in directory.glob(f"{stem}_*.md") if path != dest)
    if not stamped:
        raise FileNotFoundError(f"DeepEval markdown missing under {directory} ({stem}_*.md)")
    latest = stamped[-1]
    stamp = latest.stem.removeprefix(f"{stem}_")
    body = latest.read_text(encoding="utf-8")
    header = f"_Run: {format_deepeval_stamp(stamp)}_\n\n"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(header + body, encoding="utf-8")
    return dest


def append_abstention_section(
    dest: Path,
    *,
    total: int,
    failed: list[str],
) -> None:
    lines = [
        "",
        "## Abstention goldens",
        "",
        f"{total - len(failed)}/{total} refused as expected.",
        "",
    ]
    if failed:
        lines.append("Failed to abstain:")
        lines.extend(f"- {question}" for question in failed)
        lines.append("")
    with dest.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def write_retrieval_report(
    report: EvaluationReport[str, list[str]],
    scores: RetrievalScores,
    gate: RetrievalSettings,
    dest: Path,
    *,
    run_at: datetime | None = None,
) -> Path:
    when = run_at or datetime.now().astimezone()
    stamp = when.strftime("%Y-%m-%d %H:%M:%S %z")
    mins = gate.minimums
    rows = [
        "# Retrieval IR",
        "",
        f"_Run: {stamp}_",
        "",
        f"Pydantic Evals · k={gate.k} · {len(report.cases)} labeled goldens.",
        "",
        "| Metric | Score | Gate |",
        "|---|---:|---:|",
        f"| Recall@{gate.k} | {scores.recall_at_k:.2f} | {mins.recall_at_k:.2f} |",
        f"| Precision@{gate.k} | {scores.precision_at_k:.2f} | {mins.precision_at_k:.2f} |",
        f"| Hit Rate@{gate.k} | {scores.hit_rate_at_k:.2f} | {mins.hit_rate_at_k:.2f} |",
        f"| MRR | {scores.mrr:.2f} | {mins.mrr:.2f} |",
        f"| nDCG@{gate.k} | {scores.ndcg_at_k:.2f} | {mins.ndcg_at_k:.2f} |",
        "",
        "## Cases",
        "",
        "| Case | Query | Expected | Top sources | Recall | MRR | nDCG |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for case in report.cases:
        query = str(case.inputs).replace("|", "\\|")
        expected = str(case.expected_output or "").replace("|", "\\|")
        sources = ", ".join(str(item) for item in case.output) if case.output else ""
        rows.append(
            f"| {case.name} | {query} | {expected} | {sources} | "
            f"{_score(case.scores, 'recall_at_k'):.2f} | "
            f"{_score(case.scores, 'mrr'):.2f} | "
            f"{_score(case.scores, 'ndcg_at_k'):.2f} |"
        )
    rows.append("")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(rows), encoding="utf-8")
    return dest


def _score(scores: dict[str, object], name: str) -> float:
    result = scores[name]
    return float(result.value)
