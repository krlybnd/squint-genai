from pathlib import Path

import pytest

from agentic_eval.core.clients.catalog import catalog_blockers
from agentic_eval.core.settings import CoreSettings
from generation.settings import GenerationGates

_PROXY_ENV = (
    "LITELLM_MASTER_KEY",
    "OPENAI_API_KEY",
    "EVAL_OPENAI_API_KEY",
    "EVAL_OPENAI_BASE_URL",
    "EVAL_SUT_LITELLM_API_KEY",
    "EVAL_SUT_LITELLM_BASE_URL",
    "EVAL_CHAT_URL",
    "EVAL_API_URL",
    "EVAL_SUT_CHAT_URL",
    "EVAL_SUT_API_URL",
    "EVAL_SUT_API_KEY",
    "EVAL_SUT_INTERNAL_SERVICE_KEY",
    "API_KEY",
    "INTERNAL_SERVICE_KEY",
)


@pytest.fixture(autouse=True)
def _isolate_core_host_env(monkeypatch) -> None:
    for name in _PROXY_ENV:
        monkeypatch.delenv(name, raising=False)


def test_core_and_gates_load_from_the_same_env_file(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("EVAL_TENANT_ID=tenant-a\n", encoding="utf-8")
    monkeypatch.setenv("EVAL_TENANT_ID", "tenant-a")

    core = CoreSettings(_env_file=env_file)

    assert core.tenant_id == "tenant-a"
    assert core.chat_url == "http://localhost:8002"
    assert core.api_url == "http://localhost:8000"
    assert "cannot find" in GenerationGates().refusal_markers


def test_core_defaults_ignore_compose_dns_env(monkeypatch) -> None:
    monkeypatch.setenv("LITELLM_BASE_URL", "http://litellm:4000")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")

    core = CoreSettings()

    assert core.openai_base_url == "http://localhost:4000"
    assert core.openai_compatible_base_url == "http://localhost:4000/v1"
    assert core.chat_url == "http://localhost:8002"
    assert core.api_url == "http://localhost:8000"


def test_core_honors_eval_sut_host_aliases(monkeypatch) -> None:
    monkeypatch.setenv("EVAL_SUT_LITELLM_BASE_URL", "http://127.0.0.1:4000")
    monkeypatch.setenv("EVAL_SUT_LITELLM_API_KEY", "sk-eval-key")
    monkeypatch.setenv("EVAL_SUT_CHAT_URL", "http://127.0.0.1:8002")
    monkeypatch.setenv("EVAL_SUT_API_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("EVAL_SUT_INTERNAL_SERVICE_KEY", "internal-eval")
    monkeypatch.setenv("EVAL_TENANT_ID", "tenant-a")

    core = CoreSettings()

    assert core.openai_base_url == "http://127.0.0.1:4000"
    assert core.chat_url == "http://127.0.0.1:8002"
    assert core.api_url == "http://127.0.0.1:8000"
    assert core.auth_headers() == {
        "X-Tenant-Id": "tenant-a",
        "X-Internal-Service-Key": "internal-eval",
    }
    assert core.proxy_api_key == "sk-eval-key"


def test_core_internal_service_key_alias_from_env_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "EVAL_TENANT_ID=tenant-a\nINTERNAL_SERVICE_KEY=from-eval-env\n",
        encoding="utf-8",
    )

    core = CoreSettings(_env_file=env_file)

    assert core.auth_headers()["X-Internal-Service-Key"] == "from-eval-env"


def test_catalog_blockers_reports_missing_and_dupes() -> None:
    # Arrange
    rows = [("alpha.pdf", "d1"), ("alpha.pdf", "d2")]

    # Act
    blocked = catalog_blockers(rows, ("alpha.pdf", "beta.pdf"))

    # Assert
    assert blocked is not None
    assert "dupes" in blocked
    assert "missing" in blocked
    assert catalog_blockers([("alpha.pdf", "d1")], ("alpha.pdf",)) is None
    assert catalog_blockers([("alpha.pdf", "d1")], (str(Path("alpha.md")),)) is None
