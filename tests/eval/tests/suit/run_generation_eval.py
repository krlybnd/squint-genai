"""Generation eval as a DeepEval script (not pytest).

Tutorial: call the app on every golden, then ``evaluate(test_cases, metrics)``
so one Rich progress bar covers every labeled case at once.
https://deepeval.com/tutorials/summarization-agent/evaluation
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Sequence

from deepeval import evaluate
from deepeval.evaluate import AsyncConfig, DisplayConfig, ErrorConfig
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeElapsedColumn

from agentic_eval.core.deepeval.judge import judge_model
from agentic_eval.core.goldendata import (
    AbstentionGolden,
    LabeledGolden,
    abstention_goldens,
    labeled_goldens,
    load_goldens,
)
from agentic_eval.core.reports import (
    EVAL_REPORTS_DIR,
    GENERATION_REPORT,
    append_abstention_section,
    promote_deepeval_report,
)
from agentic_eval.modules.generation.app import answer_questions, build_eval_graph
from agentic_eval.modules.generation.evaluators import looks_like_refusal
from agentic_eval.modules.generation.types import GenerationResult
from agentic_eval.settings import EvalMode
from suit.qdrant import require_qdrant_collection
from suit.settings import eval_env_file, load_suit_settings


def _app_progress() -> Progress:
    return Progress(
        TextColumn("{task.description}"),
        BarColumn(bar_width=60),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    )


async def _call_app(
    questions: Sequence[str],
    *,
    tenant_id: str,
    graph: object,
    max_concurrent: int,
    description: str,
) -> list[GenerationResult]:
    if not questions:
        return []
    with _app_progress() as progress:
        task_id = progress.add_task(description, total=len(questions))
        return await answer_questions(
            questions,
            tenant_id=tenant_id,
            graph=graph,
            max_concurrent=max_concurrent,
            on_done=lambda: progress.advance(task_id),
        )


def main() -> int:
    if eval_env_file() is None:
        print(
            "Live eval needs tests/eval/.env — cp tests/eval/.env.example tests/eval/.env",
            file=sys.stderr,
        )
        return 2
    suit = load_suit_settings()
    if suit.mode is not EvalMode.live:
        print("Set EVAL_MODE=live in tests/eval/.env", file=sys.stderr)
        return 2
    require_qdrant_collection(url=suit.sut.qdrant_url, collection=suit.sut.qdrant_collection)

    graph = build_eval_graph(suit.sut, top_k=suit.retrieval.k)
    judge = judge_model(suit, suit.sut)
    goldens = load_goldens()
    labeled: list[LabeledGolden] = labeled_goldens(goldens)
    gate = suit.generation

    labeled_results = asyncio.run(
        _call_app(
            [golden.input for golden in labeled],
            tenant_id=suit.tenant_id,
            graph=graph,
            max_concurrent=suit.max_concurrency,
            description=f"Calling LLM app ({len(labeled)} goldens)",
        )
    )
    test_cases = [
        LLMTestCase(
            input=golden.input,
            actual_output=result.answer,
            expected_output=golden.expected_output,
            retrieval_context=result.contexts,
        )
        for golden, result in zip(labeled, labeled_results, strict=True)
    ]

    EVAL_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = evaluate(
        test_cases,
        [
            FaithfulnessMetric(
                threshold=gate.faithfulness_threshold,
                model=judge,
                async_mode=False,
            ),
            AnswerRelevancyMetric(
                threshold=gate.answer_relevancy_threshold,
                model=judge,
                async_mode=False,
            ),
        ],
        identifier="generation",
        async_config=AsyncConfig(
            run_async=True,
            max_concurrent=suit.judge_max_concurrency,
            throttle_value=suit.judge_throttle_seconds,
        ),
        display_config=DisplayConfig(
            show_indicator=True,
            print_results=True,
            inspect_after_run=False,
            file_type="md",
            file_output_dir=str(EVAL_REPORTS_DIR),
        ),
        error_config=ErrorConfig(ignore_errors=True, skip_on_missing_params=True),
    )
    promote_deepeval_report(EVAL_REPORTS_DIR, stem="generation", dest=GENERATION_REPORT)
    failed = [item for item in report.test_results if not item.success]

    abstention: list[AbstentionGolden] = abstention_goldens(goldens)
    abstention_results = asyncio.run(
        _call_app(
            [golden.input for golden in abstention],
            tenant_id=suit.tenant_id,
            graph=graph,
            max_concurrent=suit.max_concurrency,
            description=f"Calling LLM app ({len(abstention)} abstention goldens)",
        )
    )
    abstention_failed = [
        golden.input
        for golden, result in zip(abstention, abstention_results, strict=True)
        if not looks_like_refusal(result.answer, suit.generation.refusal_markers)
    ]
    for question in abstention_failed:
        print(f"abstention FAIL: {question}", file=sys.stderr)
    append_abstention_section(
        GENERATION_REPORT,
        total=len(abstention),
        failed=abstention_failed,
    )

    if failed:
        print(
            f"\n{len(failed)}/{len(report.test_results)} labeled goldens failed: "
            + "; ".join(str(item.input or "?")[:60] for item in failed),
            file=sys.stderr,
        )
    if abstention_failed:
        print("abstention failed: " + "; ".join(abstention_failed), file=sys.stderr)
    return 1 if failed or abstention_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
