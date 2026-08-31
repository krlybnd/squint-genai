"""pydantic-evals extensions (IR evaluator + evaluate wrapper)."""

from agentic_eval.core.pydantic_evals.evaluate import evaluate
from agentic_eval.core.pydantic_evals.metrics import RetrievalIR

__all__ = [
    "RetrievalIR",
    "evaluate",
]
