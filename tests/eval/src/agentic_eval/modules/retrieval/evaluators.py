"""Pydantic Evals evaluators for ranked retrieval."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from agentic_eval.modules.retrieval.metrics import RetrievalEvalCase, score_retrieval


@dataclass
class RetrievalIR(Evaluator[str, list[str]]):
    """Recall@k, Precision@k, MRR, nDCG@k against ``expected_source_file``."""

    k: int = 5

    def evaluate(self, ctx: EvaluatorContext[str, list[str]]) -> dict[str, float]:
        expected = ctx.expected_output if isinstance(ctx.expected_output, str) else ""
        scores = score_retrieval(
            RetrievalEvalCase(
                query=ctx.inputs,
                expected_source_file=expected,
                ranked_source_files=ctx.output,
                k=self.k,
            )
        )
        return scores.model_dump()
