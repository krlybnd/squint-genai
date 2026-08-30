"""Service identity defaults from installed package metadata (pyproject.toml)."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field

from agentic_shared.core.package import PackageInfo


class FrameworkDefaults(BaseModel):
    """OpenAPI / banner identity loaded from a distribution's ``pyproject.toml``."""

    package: PackageInfo = Field(
        description="Resolved name / version / description from the installed package.",
    )

    @classmethod
    def from_distribution(cls, distribution: str) -> Self:
        return cls(package=PackageInfo.from_distribution(distribution))
