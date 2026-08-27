#!/usr/bin/env bash
# cue vet + folder paths + projects.mk parity (ADR 008)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cue vet project.cue

if ! cue export project.cue -e projectsMk --out text | diff -u make/projects.mk -; then
  echo "project.cue build.* drift from make/projects.mk (run: make sync-projects-mk)" >&2
  exit 1
fi

missing=()
while IFS= read -r path; do
  [[ -z "${path}" ]] && continue
  if [[ ! -e "${path}" ]]; then
    missing+=("${path}")
  fi
done < <(cue export project.cue -e requiredFolderPathsText --out text)

if ((${#missing[@]} > 0)); then
  echo "project.cue folders missing on disk:" >&2
  printf '%s\n' "${missing[@]}" | sort | sed 's/^/  - /' >&2
  exit 1
fi

count="$(cue export project.cue -e 'len(folders)')"
echo "OK: ${count} folder entries, build lists match make/projects.mk"
