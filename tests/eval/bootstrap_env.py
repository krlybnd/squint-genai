"""Load repo-root .env so eval uses the same LiteLLM / OpenAI keys as the stack."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export "):
        stripped = stripped.removeprefix("export ").strip()
    if "=" not in stripped:
        return None
    key, _, value = stripped.partition("=")
    key = key.strip()
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return key, value


def apply_eval_env(*, override: bool = False) -> None:
    """Apply repo-root ``.env`` without clobbering variables already in the shell."""
    if not ENV_FILE.is_file():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(line)
        if parsed is None:
            continue
        key, value = parsed
        if override or key not in os.environ:
            os.environ[key] = value


def configure_llm_env_for_eval() -> None:
    """Point DeepEval / OpenAI clients at the same LiteLLM proxy as application services."""
    apply_eval_env()
    from agentic_shared.integrations.llm.settings import LLMSettings

    llm = LLMSettings()
    os.environ["OPENAI_API_KEY"] = llm.proxy_api_key
    base = llm.litellm_base_url.rstrip("/")
    os.environ["OPENAI_BASE_URL"] = f"{base}/v1"
    os.environ.setdefault("LITELLM_BASE_URL", base)
    os.environ.setdefault("LITELLM_MODEL", llm.litellm_model)
