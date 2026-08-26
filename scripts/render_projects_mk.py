#!/usr/bin/env python3
"""Render make/projects.mk project lists from project.cue build.*."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_CUE = ROOT / "project.cue"
PROJECTS_MK = ROOT / "make" / "projects.mk"

HEADER = """\
# Single source of truth for all projects in the monorepo.
# Canonical lists live in ../project.cue (build.*) — ADR 008.
# Regenerate: make sync-projects-mk | Verify: make verify-repo-map
"""

GENERATED_VARS = (
    ("PYTHON_LIBS", "pythonLibs"),
    ("PYTHON_SERVICES", "pythonServices"),
    ("PYTHON_SUITES", "pythonSuites"),
    ("NODE_LIBS", "nodeLibs"),
    ("NODE_APPS", "nodeApps"),
    ("NODE_SUITES", "nodeSuites"),
    ("PYTHON_REPORT_NAMES", "pythonReportNames"),
)

DERIVED = """
PYTHON_PROJECTS := $(PYTHON_LIBS) $(PYTHON_SERVICES)

NODE_PROJECTS   := $(NODE_LIBS) $(NODE_APPS)

# Sync/install fan-out (includes test runners)
ALL_PYTHON_SYNC := $(PYTHON_PROJECTS) $(PYTHON_SUITES)
ALL_NODE_SYNC   := $(NODE_PROJECTS) $(NODE_SUITES)

# Short names for report paths (.reports/python/<name>/, .reports/node/<name>/)
"""


def _cue_build() -> dict[str, list[str]]:
    result = subprocess.run(
        ["cue", "export", PROJECT_CUE.name, "-e", "build"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _render(build: dict[str, list[str]]) -> str:
    lines = [HEADER.rstrip(), ""]
    width = max(len(mk_name) for mk_name, _ in GENERATED_VARS)
    for mk_name, cue_name in GENERATED_VARS:
        values = " ".join(build[cue_name])
        lines.append(f"{mk_name.ljust(width)} := {values}")
    lines.append(DERIVED.rstrip())
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    content = _render(_cue_build())
    PROJECTS_MK.write_text(content, encoding="utf-8")
    print(f"Wrote {PROJECTS_MK.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
