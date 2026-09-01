"""pydantic-evals ``Dataset.evaluate`` with the display config this package always uses.

Must run on the same event loop as the HTTP client. ``evaluate_sync`` would start a
second loop and close connections opened during catalog checks.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from sys import stdout
from typing import Any

from pydantic_evals import Dataset
from pydantic_evals.reporting import EvaluationReport
from rich.console import Console


async def evaluate(
    dataset: Dataset[Any, Any],
    task: Callable[[Any], Awaitable[Any]] | Callable[[Any], Any],
    *,
    name: str,
    max_concurrency: int,
) -> EvaluationReport[Any, Any]:
    report = await dataset.evaluate(
        task,
        name=name,
        max_concurrency=max_concurrency,
        progress=True,
    )
    report.print(console=Console(file=stdout))
    return report
