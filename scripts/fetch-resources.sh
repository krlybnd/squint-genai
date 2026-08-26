#!/usr/bin/env bash
# Download demo PDFs into resources/. Not committed — see resources/README.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${ROOT}/resources"
mkdir -p "${DEST}"

UA="Mozilla/5.0 (compatible; Squint-resources/1.0; +https://github.com/krlybnd/agentic-rag-eval)"

# filename|url
FILES=(
  "attention-is-all-you-need.pdf|https://arxiv.org/pdf/1706.03762"
  "rag-lewis-2020.pdf|https://arxiv.org/pdf/2005.11401"
  "us-constitution.pdf|https://constitution.congress.gov/static/files/Literal_Print_of_Constitution_MCT_1.9.26.pdf"
  "nasa-fy2025-mission-fact-sheets.pdf|https://www.nasa.gov/wp-content/uploads/2024/03/nasa-fiscal-year-2025-mission-fact-sheets.pdf"
  "nist-ai-rmf-1.0.pdf|https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf"
)

failed=0
for entry in "${FILES[@]}"; do
  name="${entry%%|*}"
  url="${entry#*|}"
  out="${DEST}/${name}"
  if [[ -f "${out}" ]] && [[ "$(head -c 5 "${out}" 2>/dev/null || true)" == "%PDF-" ]]; then
    echo "ok  ${name} (already present)"
    continue
  fi
  echo "get ${name}"
  tmp="${out}.tmp"
  if ! curl -fsSL --retry 3 --retry-delay 2 -A "${UA}" -o "${tmp}" "${url}"; then
    echo "fail ${name}: download error from ${url}" >&2
    rm -f "${tmp}"
    failed=1
    continue
  fi
  if [[ "$(head -c 5 "${tmp}" 2>/dev/null || true)" != "%PDF-" ]]; then
    echo "fail ${name}: response is not a PDF (blocked or HTML error page)" >&2
    rm -f "${tmp}"
    failed=1
    continue
  fi
  mv "${tmp}" "${out}"
  echo "ok  ${name}"
done

if [[ "${failed}" -ne 0 ]]; then
  echo "Some PDFs failed. Download those URLs in a browser and save them under resources/." >&2
  exit 1
fi
echo "All demo PDFs are in ${DEST}"
