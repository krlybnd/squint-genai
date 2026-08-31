import os
from unittest.mock import patch

import pytest
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings

from agentic_eval.core.golden.settings import GoldenSettings
from agentic_eval.core.settings import EVAL_ROOT, CoreSettings
from generation.settings import DeepEvalSettings, GenerationGates, JudgeSettings
from retrieval.settings import RetrievalGates

_CORE_ENV = (
    "LITELLM_MASTER_KEY",
    "OPENAI_API_KEY",
    "EVAL_OPENAI_API_KEY",
    "EVAL_OPENAI_BASE_URL",
    "EVAL_SUT_LITELLM_API_KEY",
    "EVAL_SUT_LITELLM_BASE_URL",
)


@pytest.fixture(autouse=True)
def _isolate_core_env(monkeypatch) -> None:
    for name in _CORE_ENV:
        monkeypatch.delenv(name, raising=False)


def test_eval_root_is_the_eval_package() -> None:
    # Assert
    assert EVAL_ROOT.name == "eval"
    assert (EVAL_ROOT / "dataset.json").is_file()
    assert (EVAL_ROOT / ".env.example").is_file()


def test_core_settings_defaults_are_openai_compatible_localhost() -> None:
    # Arrange / Act
    with patch.dict(os.environ, {}, clear=True):
        core = CoreSettings()
        llm = LiteLLMChatSettings(_env_file=None)

    # Assert
    assert core.tenant_id == "default"
    assert core.max_concurrency == 20
    assert core.openai_base_url == "http://localhost:4000"
    assert core.openai_compatible_base_url == "http://localhost:4000/v1"
    assert core.proxy_api_key == "sk-change-me"
    assert llm.litellm_judge_model == "judge"
    assert not llm.litellm_judge_model.startswith("openai/")


def test_core_settings_honors_eval_prefix(monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("EVAL_TENANT_ID", "tenant-a")
    monkeypatch.setenv("EVAL_MAX_CONCURRENCY", "8")
    monkeypatch.setenv("EVAL_OPENAI_BASE_URL", "http://127.0.0.1:4000")
    monkeypatch.setenv("EVAL_OPENAI_API_KEY", "sk-eval-key")

    # Act
    core = CoreSettings()

    # Assert
    assert core.tenant_id == "tenant-a"
    assert core.max_concurrency == 8
    assert core.openai_base_url == "http://127.0.0.1:4000"
    assert core.proxy_api_key == "sk-eval-key"


def test_core_openai_key_aliases_litellm_master_key(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("LITELLM_MASTER_KEY=sk-from-master-key\n", encoding="utf-8")

    core = CoreSettings(_env_file=env_file)

    assert core.proxy_api_key == "sk-from-master-key"


def test_core_openai_key_aliases_eval_sut_litellm(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("EVAL_SUT_LITELLM_API_KEY=sk-from-sut\n", encoding="utf-8")

    core = CoreSettings(_env_file=env_file)

    assert core.proxy_api_key == "sk-from-sut"
    assert core.openai_base_url == "http://localhost:4000"


def test_generation_gates_own_prefix(monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("EVAL_GENERATION_ANSWER_RELEVANCY_THRESHOLD", "0.4")
    monkeypatch.setenv("EVAL_JUDGE_MODEL", "custom-judge")
    monkeypatch.setenv("EVAL_JUDGE_RETRY_MAX_ATTEMPTS", "7")
    monkeypatch.setenv("EVAL_JUDGE_RETRY_INITIAL_SECONDS", "3")
    monkeypatch.setenv("EVAL_JUDGE_RETRY_CAP_SECONDS", "45")

    # Act
    gates = GenerationGates()
    judge = JudgeSettings()
    deepeval = DeepEvalSettings()

    # Assert
    assert gates.answer_relevancy_threshold == 0.4
    assert judge.model == "custom-judge"
    assert deepeval.max_attempts == 7
    assert deepeval.initial_seconds == 3.0
    assert deepeval.cap_seconds == 45.0


def test_nested_retrieval_reads_own_prefix(monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("EVAL_RETRIEVAL_MINIMUMS_MRR", "0.9")
    monkeypatch.setenv("EVAL_RETRIEVAL_K", "8")

    # Act
    gate = RetrievalGates()

    # Assert
    assert gate.minimums.mrr == 0.9
    assert gate.k == 8


def test_golden_settings_own_prefix(monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("EVAL_GOLDEN_KNOWN_SOURCE_FILES", '["custom.pdf"]')

    # Act
    settings = GoldenSettings()

    # Assert
    assert settings.known_source_files == ("custom.pdf",)
    assert GoldenSettings().known_source_files == ("custom.pdf",)


def test_generation_and_retrieval_defaults() -> None:
    with patch.dict(os.environ, {}, clear=True):
        gates = GenerationGates()
        retrieval = RetrievalGates()
        judge = JudgeSettings()
        deepeval = DeepEvalSettings()

    assert gates.faithfulness_threshold == 0.85
    assert gates.correctness_threshold == 0.80
    assert gates.answer_relevancy_threshold == 0.70
    assert retrieval.k == 5
    assert judge.model == "judge"
    assert deepeval.max_attempts == 10
    assert deepeval.initial_seconds == 2.0
    assert deepeval.cap_seconds == 60.0
    assert GoldenSettings().known_source_files == (
        "attention-is-all-you-need.pdf",
        "rag-lewis-2020.pdf",
        "us-constitution.pdf",
        "nasa-fy2025-mission-fact-sheets.pdf",
        "nist-ai-rmf-1.0.pdf",
    )


def test_litellm_judge_does_not_fall_back_to_generate() -> None:
    config = (EVAL_ROOT.parents[1] / "operations" / "litellm" / "litellm.config.yaml").read_text(
        encoding="utf-8"
    )

    assert "fallbacks:" not in config
    assert "model_name: judge" in config
    assert "num_retries: 8" in config
