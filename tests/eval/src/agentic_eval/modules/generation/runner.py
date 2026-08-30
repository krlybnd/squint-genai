"""Shared DeepEval generation gate runner (LLM-as-judge)."""

from __future__ import annotations

import asyncio
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
    append_abstention_section,
    promote_deepeval_report,
)
from agentic_eval.modules.generation.app import answer_questions, build_eval_graph
from agentic_eval.modules.generation.evaluators import looks_like_refusal
from agentic_eval.modules.generation.types import GenerationResult
from agentic_eval.modules.generation.vault_reveal import EvalVaultReveal
from agentic_eval.profiles import ProfileConfig
from suit.settings import SuitSettings, eval_env_file


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
    vault_reveal: EvalVaultReveal | None = None,
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
            vault_reveal=vault_reveal,
        )


def run_generation_gate(suit: SuitSettings, profile: ProfileConfig) -> int:
    """Run chat graph + DeepEval Faithfulness/Relevancy judges; write markdown report."""
    judge = judge_model(suit, suit.sut)
    goldens = load_goldens(settings=profile.golden)
    labeled: list[LabeledGolden] = labeled_goldens(goldens)
    abstention: list[AbstentionGolden] = abstention_goldens(goldens)

    async def _run_app_phases() -> tuple[list[GenerationResult], list[GenerationResult]]:
        # One event loop — httpx clients in graph deps must not outlive their loop.
        graph = build_eval_graph(suit.sut, top_k=suit.retrieval.k)
        vault_reveal = EvalVaultReveal(tenant_id=suit.tenant_id, env_file=eval_env_file())
        try:
            labeled_results = await _call_app(
                [golden.input for golden in labeled],
                tenant_id=suit.tenant_id,
                graph=graph,
                max_concurrent=suit.max_concurrency,
                description=f"[{profile.name}] LLM app ({len(labeled)} goldens)",
                vault_reveal=vault_reveal,
            )
            abstention_results = await _call_app(
                [golden.input for golden in abstention],
                tenant_id=suit.tenant_id,
                graph=graph,
                max_concurrent=suit.max_concurrency,
                description=f"[{profile.name}] LLM app ({len(abstention)} abstention goldens)",
                vault_reveal=vault_reveal,
            )
            return labeled_results, abstention_results
        finally:
            await vault_reveal.aclose()

    labeled_results, abstention_results = asyncio.run(_run_app_phases())
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
                threshold=profile.generation_faithfulness_threshold,
                model=judge,
                async_mode=False,
            ),
            AnswerRelevancyMetric(
                threshold=profile.generation_answer_relevancy_threshold,
                model=judge,
                async_mode=False,
            ),
        ],
        identifier=profile.deepeval_identifier,
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
    promote_deepeval_report(
        EVAL_REPORTS_DIR,
        stem=profile.deepeval_identifier,
        dest=profile.generation_report,
    )
    failed = [item for item in report.test_results if not item.success]

    abstention_failed = [
        golden.input
        for golden, result in zip(abstention, abstention_results, strict=True)
        if not looks_like_refusal(result.answer, suit.generation.refusal_markers)
    ]
    append_abstention_section(
        profile.generation_report,
        total=len(abstention),
        failed=abstention_failed,
    )

    if failed:
        import sys

        print(
            f"\n[{profile.name}] {len(failed)}/{len(report.test_results)} labeled goldens failed: "
            + "; ".join(str(item.input or "?")[:60] for item in failed),
            file=sys.stderr,
        )
    if abstention_failed:
        import sys

        msg = f"[{profile.name}] abstention failed: " + "; ".join(abstention_failed)
        print(msg, file=sys.stderr)
    return 1 if failed or abstention_failed else 0
