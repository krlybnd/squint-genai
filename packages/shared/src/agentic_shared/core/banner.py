"""Startup ASCII banner printed to stdout for every Python service."""

from __future__ import annotations

import sys
from typing import TextIO

LOGO = """\
▌   ▜   ▌    ▌
▙▘▛▘▐ ▌▌▛▌▛▌▛▌
▛▖▌ ▐▖▙▌▙▌▌▌▙▌
      ▄▌      """


def render_startup_banner(service: str, version: str = "0.1.0") -> str:
    return f"{LOGO}\n  {service}  v{version}\n"


def print_startup_banner(
    service: str,
    version: str = "0.1.0",
    *,
    stream: TextIO | None = None,
) -> None:
    out = sys.stdout if stream is None else stream
    out.write(render_startup_banner(service, version))
    out.flush()
