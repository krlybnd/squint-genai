from types import SimpleNamespace

import pytest

from agentic_eval.modules.generation.settings import DEFAULT_REFUSAL_MARKERS
from agentic_eval.settings import EvalMode
from suit.qdrant import require_qdrant_collection
from suit.settings import SUIT_REFUSAL_MARKERS, SuitSettings, SutSettings

_PROXY_ENV = (
    "OPENAI_API_KEY",
    "LITELLM_MASTER_KEY",
    "EVAL_SUT_LITELLM_API_KEY",
    "EVAL_SUT_LITELLM_BASE_URL",
    "EVAL_SUT_QDRANT_URL",
    "EVAL_SUT_QDRANT_COLLECTION",
    "EVAL_SUT_EMBEDDING_MODEL",
)


@pytest.fixture(autouse=True)
def _isolate_sut_env(monkeypatch) -> None:
    for name in _PROXY_ENV:
        monkeypatch.delenv(name, raising=False)


def test_suit_settings_extend_eval_and_sut(monkeypatch, tmp_path) -> None:
    # Arrange
    env_file = tmp_path / ".env"
    env_file.write_text("EVAL_MODE=mock\n", encoding="utf-8")
    monkeypatch.setenv("EVAL_MODE", "live")

    # Act
    suit = SuitSettings(_env_file=env_file, sut=SutSettings(_env_file=env_file))

    # Assert
    assert suit.mode is EvalMode.live
    assert suit.sut.litellm_base_url == "http://localhost:4000"
    assert suit.sut.qdrant_url == "http://localhost:6333"
    assert set(DEFAULT_REFUSAL_MARKERS) <= set(suit.generation.refusal_markers)
    assert suit.generation.refusal_markers == SUIT_REFUSAL_MARKERS


def test_sut_defaults_ignore_compose_dns_env(monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("LITELLM_BASE_URL", "http://litellm:4000")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")

    # Act
    sut = SutSettings()

    # Assert
    assert sut.litellm_base_url == "http://localhost:4000"
    assert sut.qdrant_url == "http://localhost:6333"
    assert sut.qdrant_collection == "agentic_rag_eval_hybrid"
    assert sut.embedding_model == "embed"
    assert sut.rerank_model == "rerank"
    assert sut.openai_compatible_base_url == "http://localhost:4000/v1"


def test_sut_honors_eval_sut_prefix(monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("EVAL_SUT_LITELLM_BASE_URL", "http://127.0.0.1:4000")
    monkeypatch.setenv("EVAL_SUT_QDRANT_URL", "http://127.0.0.1:6333")
    monkeypatch.setenv("EVAL_SUT_EMBEDDING_MODEL", "custom-embed")
    monkeypatch.setenv("EVAL_SUT_QDRANT_COLLECTION", "stack_collection")
    monkeypatch.setenv("EVAL_SUT_LITELLM_API_KEY", "sk-eval-key")

    # Act
    sut = SutSettings()

    # Assert
    assert sut.litellm_base_url == "http://127.0.0.1:4000"
    assert sut.qdrant_url == "http://127.0.0.1:6333"
    assert sut.embedding_model == "custom-embed"
    assert sut.qdrant_collection == "stack_collection"
    assert sut.proxy_api_key == "sk-eval-key"


def test_sut_reads_api_key_from_eval_env_file(tmp_path) -> None:
    # Arrange
    env_file = tmp_path / ".env"
    env_file.write_text(
        "EVAL_SUT_LITELLM_API_KEY=sk-from-eval-env\nLITELLM_BASE_URL=http://litellm:4000\n",
        encoding="utf-8",
    )

    # Act
    sut = SutSettings(_env_file=env_file)

    # Assert
    assert sut.litellm_api_key == "sk-from-eval-env"
    assert sut.litellm_base_url == "http://localhost:4000"


def test_sut_empty_prefixed_key_falls_through_to_openai_api_key(tmp_path) -> None:
    # Arrange
    env_file = tmp_path / ".env"
    env_file.write_text(
        "EVAL_SUT_LITELLM_API_KEY=\nOPENAI_API_KEY=sk-from-openai-alias\n",
        encoding="utf-8",
    )

    # Act
    sut = SutSettings(_env_file=env_file)

    # Assert
    assert sut.proxy_api_key == "sk-from-openai-alias"


def test_sut_empty_keys_keep_placeholder_default(tmp_path) -> None:
    # Arrange
    env_file = tmp_path / ".env"
    env_file.write_text("EVAL_SUT_LITELLM_API_KEY=\nOPENAI_API_KEY=\n", encoding="utf-8")

    # Act
    sut = SutSettings(_env_file=env_file)

    # Assert
    assert sut.litellm_api_key == "sk-change-me"


def test_require_qdrant_collection_ok_when_present(monkeypatch) -> None:
    # Arrange
    class _Collections:
        collections = [SimpleNamespace(name="agentic_rag_eval")]

    monkeypatch.setattr(
        "suit.qdrant.QdrantClient",
        lambda url: SimpleNamespace(get_collections=lambda: _Collections()),
    )

    # Act
    names = require_qdrant_collection(
        url="http://localhost:6333",
        collection="agentic_rag_eval",
    )

    # Assert
    assert names == ["agentic_rag_eval"]


def test_require_qdrant_collection_lists_available_when_missing(monkeypatch) -> None:
    # Arrange
    class _Collections:
        collections = [SimpleNamespace(name="agentic_rag_eval")]

    monkeypatch.setattr(
        "suit.qdrant.QdrantClient",
        lambda url: SimpleNamespace(get_collections=lambda: _Collections()),
    )

    # Act / Assert
    with pytest.raises(RuntimeError, match="Available: agentic_rag_eval"):
        require_qdrant_collection(
            url="http://localhost:6333",
            collection="agentic_rag_eval_hybrid",
        )
