#!/bin/sh
# Trigger API reindex-all. Waits until api /health is up (bootstrap after app start).
# OPTIONAL_INDEX=1 skips instead of failing when the wait times out.
set -eu

: "${API_BASE:=http://localhost:8000}"
: "${API_KEY:=dev-admin-key-change-me}"
: "${INTERNAL_SERVICE_KEY:=dev-internal-service-key-change-me}"
: "${TENANT_ID:=default}"
OPTIONAL_INDEX="${OPTIONAL_INDEX:-0}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-180}"

elapsed=0
until curl -sf -o /dev/null "${API_BASE}/health"; do
  if [ "${elapsed}" -ge "${WAIT_TIMEOUT}" ]; then
    if [ "${OPTIONAL_INDEX}" = "1" ]; then
      echo "api not ready at ${API_BASE}; skip index"
      exit 0
    fi
    echo "api not ready at ${API_BASE}" >&2
    exit 1
  fi
  sleep 2
  elapsed=$((elapsed + 2))
done

echo "api: reindex all (${API_BASE})"
curl -fsS -X POST "${API_BASE}/v1/admin/index" \
  -H "X-API-Key: ${API_KEY}" \
  -H "X-Internal-Service-Key: ${INTERNAL_SERVICE_KEY}" \
  -H "X-Tenant-Id: ${TENANT_ID}"
echo
