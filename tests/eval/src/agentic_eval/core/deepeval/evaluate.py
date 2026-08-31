"""DeepEval ``evaluate()`` with the display / error config this package always uses."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from deepeval import evaluate as deepeval_evaluate
from deepeval.evaluate import AsyncConfig, DisplayConfig, ErrorConfig
from deepeval.evaluate.types import EvaluationResult
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase


def evaluate(
    cases: Sequence[LLMTestCase],
    metrics: Sequence[BaseMetric],
    *,
    identifier: str,
    reports_dir: Path,
    max_concurrent: int,
    throttle_seconds: float,
) -> EvaluationResult:
    return deepeval_evaluate(
        list(cases),
        list(metrics),
        identifier=identifier,
        async_config=AsyncConfig(
            run_async=True,
            max_concurrent=max_concurrent,
            throttle_value=throttle_seconds,
        ),
        display_config=DisplayConfig(
            show_indicator=True,
            print_results=True,
            inspect_after_run=False,
            file_type="md",
            file_output_dir=str(reports_dir),
        ),
        error_config=ErrorConfig(skip_on_missing_params=True),
    )
