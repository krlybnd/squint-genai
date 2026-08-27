from __future__ import annotations

import os

import pytest

from agentic_eval.settings import EvalMode
from suit.qdrant import require_qdrant_collection
from suit.settings import SuitSettings, eval_env_file, load_suit_settings


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    skip = pytest.mark.skip(
        reason="Live eval needs EVAL_MODE=live and tests/eval/.env (cp .env.example .env)",
    )
    live = os.getenv("EVAL_MODE") == "live" or load_suit_settings().mode is EvalMode.live
    for item in items:
        item.add_marker(pytest.mark.eval)
        item.add_marker(pytest.mark.integration)
        if not live:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def suit():
    if eval_env_file() is None:
        pytest.fail("Live eval needs tests/eval/.env — cp tests/eval/.env.example tests/eval/.env")
    return load_suit_settings()


@pytest.fixture(scope="session", autouse=True)
def indexed_corpus(suit: SuitSettings) -> None:
    """Fail fast when EVAL_SUT_QDRANT_COLLECTION is missing from the live Qdrant."""
    if suit.mode is not EvalMode.live:
        return
    try:
        require_qdrant_collection(
            url=suit.sut.qdrant_url,
            collection=suit.sut.qdrant_collection,
        )
    except RuntimeError as exc:
        pytest.fail(str(exc))
