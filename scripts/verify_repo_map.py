#!/usr/bin/env python3
"""Validate project.cue against the filesystem and make/projects.mk."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_CUE = ROOT / "project.cue"
PROJECTS_MK = ROOT / "make" / "projects.mk"

MK_VARS = (
    "PYTHON_LIBS",
    "PYTHON_SERVICES",
    "PYTHON_SUITES",
    "NODE_LIBS",
    "NODE_APPS",
    "NODE_SUITES",
    "PYTHON_REPORT_NAMES",
)


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def _cue_export(expression: str) -> object:
    result = subprocess.run(
        ["cue", "export", PROJECT_CUE.name, "-e", expression],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _parse_projects_mk() -> dict[str, list[str]]:
    text = PROJECTS_MK.read_text(encoding="utf-8")
    parsed: dict[str, list[str]] = {}
    for name in MK_VARS:
        match = re.search(rf"^{name}\s*:=\s*(.+)$", text, re.MULTILINE)
        if not match:
            raise SystemExit(f"make/projects.mk: missing {name}")
        values = match.group(1).strip().split()
        parsed[name] = values
    return parsed


def _lists_match(cue_build: dict[str, object], mk: dict[str, list[str]]) -> list[str]:
    errors: list[str] = []
    mapping = {
        "pythonLibs": "PYTHON_LIBS",
        "pythonServices": "PYTHON_SERVICES",
        "pythonSuites": "PYTHON_SUITES",
        "nodeLibs": "NODE_LIBS",
        "nodeApps": "NODE_APPS",
        "nodeSuites": "NODE_SUITES",
        "pythonReportNames": "PYTHON_REPORT_NAMES",
    }
    for cue_key, mk_key in mapping.items():
        cue_vals = list(cue_build[cue_key])  # type: ignore[index]
        mk_vals = mk[mk_key]
        if cue_vals != mk_vals:
            errors.append(
                f"{mk_key}: cue={cue_vals!r} != projects.mk={mk_vals!r} "
                f"(run: make sync-projects-mk)"
            )
    return errors


def main() -> int:
    _run(["cue", "vet", PROJECT_CUE.name])

    folders = _cue_export("folders")
    missing = [path for path in folders if not (ROOT / path).exists()]
    if missing:
        print("project.cue folders missing on disk:", file=sys.stderr)
        for path in sorted(missing):
            print(f"  - {path}", file=sys.stderr)
        return 1

    cue_build = _cue_export("build")
    mk = _parse_projects_mk()
    drift_errors = _lists_match(cue_build, mk)
    if drift_errors:
        print("project.cue build.* drift from make/projects.mk:", file=sys.stderr)
        for error in drift_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"OK: {len(folders)} folder entries, build lists match make/projects.mk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
