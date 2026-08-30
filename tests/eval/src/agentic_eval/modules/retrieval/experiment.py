"""Tier 1 retrieval IR experiment."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.reporting import EvaluationReport

from agentic_eval.core.goldendata import (
    Golden,
    GoldenSettings,
    case_name,
    labeled_goldens,
    load_goldens,
)
from agentic_eval.core.protocols import HostStack
from agentic_eval.modules.retrieval.evaluators import RetrievalIR
from agentic_eval.modules.retrieval.metrics import RetrievalScores
from agentic_eval.modules.retrieval.settings import RetrievalSettings
from agentic_eval.settings import EvalSettings


def assert_retrieval_gate(
    report: EvaluationReport[str, list[str]],
    gate: RetrievalSettings,
) -> RetrievalScores:
    averages = report.averages()
    assert averages is not None, "retrieval experiment produced no scores"
    scores = RetrievalScores.model_validate(
        {name: float(averages.scores[name]) for name in RetrievalScores.model_fields}
    )
    scores.assert_at_least(gate.minimums)
    return scores


@dataclass(frozen=True)
class RetrievalExperiment:
    name: str = "retrieval_ir"

    def dataset(
        self,
        settings: EvalSettings,
        goldens: Sequence[Golden] | None = None,
        *,
        golden_settings: GoldenSettings | None = None,
        stem_match: bool = False,
    ) -> Dataset[str, list[str]]:
        loaded = (
            goldens
            if goldens is not None
            else load_goldens(settings=golden_settings or settings.golden)
        )
        labeled = labeled_goldens(list(loaded))
        return Dataset(
            name=self.name,
            cases=[
                Case(
                    name=case_name(index, item.input),
                    inputs=item.input,
                    expected_output=item.expected_source_file,
                )
                for index, item in enumerate(labeled, start=1)
            ],
            evaluators=[RetrievalIR(k=settings.retrieval.k, stem_match=stem_match)],
        )

    def run(
        self,
        settings: EvalSettings,
        stack: HostStack,
        *,
        progress: bool = True,
        golden_settings: GoldenSettings | None = None,
        stem_match: bool = False,
    ) -> EvaluationReport[str, list[str]]:
        async def task(question: str) -> list[str]:
            deps = stack.to_graph_deps(top_k=settings.retrieval.k)
            result = await deps.retrieval.search_documents_with_meta(
                question,
                top_k=settings.retrieval.k,
                tenant_id=settings.tenant_id,
            )
            return [chunk.source_file for chunk in result.chunks if chunk.source_file]

        return self.dataset(
            settings,
            golden_settings=golden_settings,
            stem_match=stem_match,
        ).evaluate_sync(
            task,
            max_concurrency=settings.max_concurrency,
            progress=progress,
        )

    def assert_gate(
        self,
        report: EvaluationReport[str, list[str]],
        settings: EvalSettings,
    ) -> RetrievalScores:
        return assert_retrieval_gate(report, settings.retrieval)
