#!/usr/bin/env bash
set -euo pipefail

if ! command -v cue >/dev/null 2>&1; then
  echo "cue CLI required for verify-repo-map — install: go install cuelang.org/go/cmd/cue@v0.11.0" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
make -C "$ROOT" verify-repo-map
