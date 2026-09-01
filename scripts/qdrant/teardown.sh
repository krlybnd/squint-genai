#!/bin/sh
# Delete the Qdrant collection used by retrieval.
set -eu

: "${QDRANT_URL:=http://qdrant:6333}"
: "${QDRANT_COLLECTION:=agentic_rag_eval_hybrid}"

url="${QDRANT_URL%/}/collections/${QDRANT_COLLECTION}"
code="$(curl -sS -o /dev/null -w '%{http_code}' -X DELETE "$url" || echo 000)"
case "$code" in
  200|404) echo "qdrant: collection ${QDRANT_COLLECTION} cleared (${code})" ;;
  *) echo "qdrant: failed to delete ${QDRANT_COLLECTION}: HTTP ${code}" >&2; exit 1 ;;
esac
