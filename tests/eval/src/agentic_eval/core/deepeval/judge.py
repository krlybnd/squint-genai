"""LiteLLM-backed DeepEval OpenAIModel (judge alias, not generate)."""

from __future__ import annotations

from deepeval.models import OpenAIModel

from agentic_eval.core.protocols import HostStack
from agentic_eval.settings import EvalSettings


def judge_model(settings: EvalSettings, stack: HostStack) -> OpenAIModel:
    settings.deepeval.apply()
    alias = settings.judge_model.strip() or "judge"
    api_key = stack.proxy_api_key.strip()
    if not api_key:
        raise ValueError(
            "LiteLLM proxy API key is empty. Set LITELLM_MASTER_KEY or "
            "EVAL_SUT_LITELLM_API_KEY in tests/eval/.env to the bearer "
            "token the stack uses (repo-root LITELLM_MASTER_KEY)."
        )
    return OpenAIModel(
        model=alias,
        api_key=api_key,
        base_url=stack.openai_compatible_base_url,
    )
