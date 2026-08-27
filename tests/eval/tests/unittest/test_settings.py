import os
from unittest.mock import patch

from agentic_shared.integrations.llm.settings import LLMSettings

from agentic_eval.core.goldendata.settings import DEFAULT_SOURCE_FILES, GoldenSettings
from agentic_eval.core.goldendata.settings import EVAL_ROOT as GOLDEN_ROOT
from agentic_eval.modules.retrieval.settings import RetrievalSettings
from agentic_eval.settings import EVAL_ROOT, EvalMode, EvalSettings


def test_eval_root_is_the_eval_package() -> None:
    # Assert
    assert EVAL_ROOT == GOLDEN_ROOT
    assert EVAL_ROOT.name == "eval"
    assert (EVAL_ROOT / "dataset.json").is_file()
    assert (EVAL_ROOT / ".env.example").is_file()


def test_eval_settings_defaults_use_judge_alias_not_generator() -> None:
    # Arrange / Act
    with patch.dict(os.environ, {}, clear=True):
        settings = EvalSettings()
        llm = LLMSettings(_env_file=None)

    # Assert
    assert settings.mode is EvalMode.mock
    assert settings.judge_model == llm.litellm_judge_model
    assert settings.judge_model != llm.litellm_model
    assert settings.max_concurrency == 20
    assert settings.judge_max_concurrency == 1
    assert settings.judge_throttle_seconds == 2.0
    assert not settings.judge_model.startswith("openai/")
    assert settings.retrieval.k == 5
    assert settings.generation.faithfulness_threshold == 0.70
    assert settings.golden.known_source_files == DEFAULT_SOURCE_FILES


def test_eval_settings_honors_eval_prefix(monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("EVAL_MODE", "live")
    monkeypatch.setenv("EVAL_TENANT_ID", "tenant-a")
    monkeypatch.setenv("EVAL_JUDGE_MODEL", "custom-judge")
    monkeypatch.setenv("EVAL_RETRIEVAL_K", "8")
    monkeypatch.setenv("EVAL_GENERATION_ANSWER_RELEVANCY_THRESHOLD", "0.4")

    # Act
    settings = EvalSettings()

    # Assert
    assert settings.mode is EvalMode.live
    assert settings.tenant_id == "tenant-a"
    assert settings.judge_model == "custom-judge"
    assert settings.retrieval.k == 8
    assert settings.generation.answer_relevancy_threshold == 0.4


def test_nested_retrieval_reads_own_prefix(monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("EVAL_RETRIEVAL_MINIMUMS_MRR", "0.9")

    # Act
    gate = RetrievalSettings()

    # Assert
    assert gate.minimums.mrr == 0.9


def test_golden_settings_own_prefix(monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("EVAL_GOLDEN_KNOWN_SOURCE_FILES", '["custom.pdf"]')

    # Act
    settings = GoldenSettings()
    nested = EvalSettings()

    # Assert
    assert settings.known_source_files == ("custom.pdf",)
    assert nested.golden.known_source_files == ("custom.pdf",)
