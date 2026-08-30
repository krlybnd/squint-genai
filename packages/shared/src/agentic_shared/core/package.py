"""Distribution metadata from installed packages (pyproject.toml via importlib)."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, metadata, version
from typing import Self

from pydantic import BaseModel, Field


class PackageInfo(BaseModel):
    """Name / version / summary as published in the package's ``pyproject.toml``."""

    name: str = Field(description="PEP 621 distribution name (``[project].name``).")
    version: str = Field(description="PEP 621 package version (``[project].version``).")
    description: str = Field(
        default="",
        description="PEP 621 package summary (``[project].description``).",
    )

    @classmethod
    def from_distribution(
        cls,
        distribution: str,
        *,
        fallback_name: str | None = None,
    ) -> Self:
        """Load installed distribution metadata; fall back if not installed yet."""
        try:
            pkg = metadata(distribution)
            return cls(
                name=pkg["Name"],
                version=version(distribution),
                description=(pkg.get("Summary") or "").strip(),
            )
        except PackageNotFoundError:
            return cls(
                name=fallback_name or distribution,
                version="0.0.0",
                description="",
            )
