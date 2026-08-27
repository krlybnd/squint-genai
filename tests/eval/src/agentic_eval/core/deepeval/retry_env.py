"""Set DeepEval retry env before any ``deepeval`` import.

Defaults (2 attempts, 5s cap) exhaust on gpt-4o 429s and surface as
``RetryError[RateLimitError]`` — a quality FAIL, not a retry.
"""

from __future__ import annotations

import os

JUDGE_RETRY_ENV: dict[str, str] = {
    "DEEPEVAL_RETRY_MAX_ATTEMPTS": "10",
    "DEEPEVAL_RETRY_INITIAL_SECONDS": "2",
    "DEEPEVAL_RETRY_CAP_SECONDS": "60",
}


def configure_judge_retries() -> None:
    for key, value in JUDGE_RETRY_ENV.items():
        os.environ.setdefault(key, value)
