"""DeepEval extensions (metrics + evaluate wrapper)."""

from agentic_eval.core.deepeval.evaluate import evaluate
from agentic_eval.core.deepeval.metrics import AbstentionMetric, RequiredPhrasesMetric

__all__ = [
    "AbstentionMetric",
    "RequiredPhrasesMetric",
    "evaluate",
]
