"""Startup ASCII banner printed to stdout for every Python service."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import TextIO

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from agentic_shared.core.package import PackageInfo


def _templates_dir() -> Path:
    """Resolve Jinja templates: checkout ``packages/shared/templates``, else wheel data."""
    checkout = Path(__file__).resolve().parents[3] / "templates"
    if (checkout / "banner.j2").is_file():
        return checkout
    packaged = Path(__file__).resolve().parents[1] / "templates"
    if (packaged / "banner.j2").is_file():
        return packaged
    raise FileNotFoundError(
        "banner.j2 not found under packages/shared/templates or agentic_shared/templates"
    )


@lru_cache(maxsize=1)
def _template_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(_templates_dir()),
        autoescape=False,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def print_startup_banner(
    package: PackageInfo | str,
    *,
    stream: TextIO | None = None,
    shared: PackageInfo | str | None = "agentic-shared",
) -> None:
    """Render ``templates/banner.j2`` with package identity and print it."""
    info = package if isinstance(package, PackageInfo) else PackageInfo.from_distribution(package)
    shared_info: PackageInfo | None = None
    if shared is not None:
        shared_info = (
            shared if isinstance(shared, PackageInfo) else PackageInfo.from_distribution(shared)
        )
        if shared_info.name == info.name:
            shared_info = None

    text = (
        _template_env()
        .get_template("banner.j2")
        .render(
            package=info,
            shared=shared_info,
        )
    )
    out = sys.stdout if stream is None else stream
    out.write(text)
    out.flush()
