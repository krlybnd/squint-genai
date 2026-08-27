import inspect
from types import SimpleNamespace

import pytest
from deepeval.config.settings import get_settings

from agentic_eval.core.deepeval.judge import judge_model
from agentic_eval.core.deepeval.settings import DeepEvalSettings
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
    assert "deepeval.apply" in adapter
    assert 'file_type="md"' in source
    assert "file_output_dir" in source
    assert 'identifier="generation"' in source
    assert "promote_deepeval_report" in source
    assert "os.environ" not in adapter
    assert "os.environ" not in inspect.getsource(DeepEvalSettings.apply)
    assert "retry_env" not in source
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


def test_deepeval_settings_apply_retries_on_live_singleton(monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("EVAL_JUDGE_RETRY_MAX_ATTEMPTS", "7")
    monkeypatch.setenv("EVAL_JUDGE_RETRY_INITIAL_SECONDS", "3")
    monkeypatch.setenv("EVAL_JUDGE_RETRY_CAP_SECONDS", "45")
    settings = DeepEvalSettings()
    live = get_settings()
    before = (
        live.DEEPEVAL_RETRY_MAX_ATTEMPTS,
        live.DEEPEVAL_RETRY_INITIAL_SECONDS,
        live.DEEPEVAL_RETRY_CAP_SECONDS,
    )

    # Act
    try:
        settings.apply()

        # Assert
        assert settings.max_attempts == 7
        assert live.DEEPEVAL_RETRY_MAX_ATTEMPTS == 7
        assert live.DEEPEVAL_RETRY_INITIAL_SECONDS == 3.0
        assert live.DEEPEVAL_RETRY_CAP_SECONDS == 45.0
    finally:
        live.DEEPEVAL_RETRY_MAX_ATTEMPTS = before[0]
        live.DEEPEVAL_RETRY_INITIAL_SECONDS = before[1]
        live.DEEPEVAL_RETRY_CAP_SECONDS = before[2]


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
