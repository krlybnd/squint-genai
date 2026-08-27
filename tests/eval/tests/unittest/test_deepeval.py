import inspect
import os
from types import SimpleNamespace

import pytest

from agentic_eval.core.deepeval.judge import judge_model
from agentic_eval.core.deepeval.retry_env import JUDGE_RETRY_ENV, configure_judge_retries
from agentic_eval.settings import EVAL_ROOT, EvalSettings


def test_generation_runner_uses_deepeval_evaluate() -> None:
    # Arrange
    source = (EVAL_ROOT / "tests" / "suit" / "run_generation_eval.py").read_text(encoding="utf-8")
    adapter = inspect.getsource(judge_model)

    # Assert
    assert "evaluate(" in source
    assert "assert_test" not in source
    assert "show_indicator=True" in source
    assert "inspect_after_run=False" in source
    assert "ignore_errors=True" in source
    assert "run_async=True" in source
    assert "judge_max_concurrency" in source
    assert "judge_throttle_seconds" in source
    assert "async_mode=False" in source
    assert "configure_judge_retries" in source
    assert "DEEPEVAL_RETRY_MAX_ATTEMPTS" in (
        EVAL_ROOT / "src" / "agentic_eval" / "core" / "deepeval" / "retry_env.py"
    ).read_text(encoding="utf-8")
    assert "answer_questions" in source
    assert "[index/" not in source
    assert "FaithfulnessMetric" in source
    assert "AnswerRelevancyMetric" in source
    assert "ContextualPrecisionMetric" not in source
    assert "ContextualRecallMetric" not in source
    assert "OpenAIModel" in adapter


def test_live_retrieval_makefile_prints_ir_report() -> None:
    # Arrange
    makefile = (EVAL_ROOT / "Makefile").read_text(encoding="utf-8")

    # Assert — pytest -q hides report.print() / MRR
    assert "tests/suit/test_retrieval_eval.py" in makefile
    assert "pytest -s tests/suit/test_retrieval_eval.py" in makefile
    assert "eval-live: run-live" in makefile


def test_configure_judge_retries_does_not_override_existing(monkeypatch) -> None:
    # Arrange
    monkeypatch.delenv("DEEPEVAL_RETRY_CAP_SECONDS", raising=False)
    monkeypatch.setenv("DEEPEVAL_RETRY_MAX_ATTEMPTS", "3")

    # Act
    configure_judge_retries()

    # Assert
    assert os.environ["DEEPEVAL_RETRY_MAX_ATTEMPTS"] == "3"
    assert os.environ["DEEPEVAL_RETRY_CAP_SECONDS"] == JUDGE_RETRY_ENV["DEEPEVAL_RETRY_CAP_SECONDS"]


def test_litellm_judge_does_not_fall_back_to_generate() -> None:
    # Arrange
    config = (EVAL_ROOT.parents[1] / "operations" / "litellm" / "litellm.config.yaml").read_text(
        encoding="utf-8"
    )

    # Assert
    assert "fallbacks:" not in config
    assert "model_name: judge" in config
    assert "num_retries: 8" in config


def test_judge_model_rejects_empty_key() -> None:
    # Arrange
    stack = SimpleNamespace(
        openai_compatible_base_url="http://localhost:4000/v1",
        proxy_api_key="   ",
    )

    # Act / Assert
    with pytest.raises(ValueError, match="tests/eval/.env"):
        judge_model(EvalSettings(), stack)
