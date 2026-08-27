"""Metrics and thresholds for the RAG eval suite.

Generation metrics stay at 0.7. Retrieval metrics are 0.6: they score the
hybrid candidate pool + rerank (`candidate_top_k` → `top_k`), which is the
part of the stack the golden dataset is meant to pressure.

Tier-1 IR metrics (Recall@k, MRR, nDCG@k) live in ``retrieval_metrics.py`` and
``test_retrieval_eval.py`` — deterministic, no judge LLM.
"""

from __future__ import annotations

from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    FaithfulnessMetric,
)
from deepeval.metrics.base_metric import BaseMetric

from bootstrap_env import configure_llm_env_for_eval


def judge_model() -> str:
    configure_llm_env_for_eval()
    from agentic_shared.integrations.llm.settings import LLMSettings

    return f"openai/{LLMSettings().litellm_model}"


def rag_metrics() -> list[BaseMetric]:
    configure_llm_env_for_eval()
    model = judge_model()
    return [
        ContextualPrecisionMetric(threshold=0.6, model=model),
        ContextualRecallMetric(threshold=0.6, model=model),
        FaithfulnessMetric(threshold=0.7, model=model),
        AnswerRelevancyMetric(threshold=0.7, model=model),
    ]
