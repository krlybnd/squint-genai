"""Shared httpx settings for generated OpenAPI Client constructors."""

from __future__ import annotations

from typing import Any

import httpx

TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)


def client_kwargs(
    base_url: str, *, headers: dict[str, str], max_connections: int
) -> dict[str, Any]:
    return {
        "base_url": base_url.rstrip("/"),
        "headers": headers,
        "timeout": TIMEOUT,
        "raise_on_unexpected_status": True,
        "httpx_args": {
            "limits": httpx.Limits(
                max_connections=max_connections + 4,
                max_keepalive_connections=max_connections,
            )
        },
    }
