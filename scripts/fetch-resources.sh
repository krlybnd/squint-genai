#!/usr/bin/env bash
# Download demo PDFs into resources/. Catalog: DEMO_RESOURCES (tools/ops/Makefile).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${ROOT}/resources"
UA="Mozilla/5.0 (compatible; Squint-resources/1.0; +https://github.com/krlybnd/squint-genai)"
CATALOG_FILE=""

usage() {
  echo "Usage: fetch-resources.sh [--file catalog]  (or DEMO_RESOURCES env / stdin)" >&2
  echo "Catalog lines: filename|url" >&2
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --file) CATALOG_FILE="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

catalog() {
  if [ -n "${CATALOG_FILE}" ] && [ -f "${CATALOG_FILE}" ]; then
    cat "${CATALOG_FILE}"
  elif [ -n "${DEMO_RESOURCES:-}" ]; then
    printf '%s\n' "${DEMO_RESOURCES}"
  elif [ ! -t 0 ]; then
    cat
  else
    echo "Missing resource catalog (DEMO_RESOURCES, --file, or stdin)" >&2
    exit 1
  fi
}

mkdir -p "${DEST}"
tmp="$(mktemp)"
catalog > "${tmp}"

failed=0
while IFS= read -r line || [ -n "${line}" ]; do
  case "${line}" in
    ''|\#*) continue ;;
  esac
  name="${line%%|*}"
  url="${line#*|}"
  out="${DEST}/${name}"
  if [ -f "${out}" ] && [ "$(head -c 5 "${out}" 2>/dev/null || true)" = "%PDF-" ]; then
    echo "ok  ${name} (already present)"
    continue
  fi
  echo "get ${name}"
  part="${out}.tmp"
  if ! curl -fsSL --retry 3 --retry-delay 2 -A "${UA}" -o "${part}" "${url}"; then
    echo "fail ${name}: download error from ${url}" >&2
    rm -f "${part}"
    failed=1
    continue
  fi
  if [ "$(head -c 5 "${part}" 2>/dev/null || true)" != "%PDF-" ]; then
    echo "fail ${name}: response is not a PDF (blocked or HTML error page)" >&2
    rm -f "${part}"
    failed=1
    continue
  fi
  mv "${part}" "${out}"
  echo "ok  ${name}"
done < "${tmp}"
rm -f "${tmp}"

if [ "${failed}" -ne 0 ]; then
  echo "Some PDFs failed. Download those URLs in a browser and save them under resources/." >&2
  exit 1
fi
echo "All demo PDFs are in ${DEST}"
