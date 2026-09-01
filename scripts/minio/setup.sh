#!/usr/bin/env bash
# Ensure MinIO bucket + CORS. Compose starts ops after minio is healthy.
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

: "${MINIO_ENDPOINT:=minio:9000}"
: "${MINIO_ACCESS_KEY:=minioadmin}"
: "${MINIO_SECRET_KEY:=minioadmin}"
: "${MINIO_BUCKET:=documents}"

if [ -z "${MINIO_CORS_FILE:-}" ]; then
  if [ -f "${SCRIPT_DIR}/../../operations/minio/cors.json" ]; then
    MINIO_CORS_FILE="${SCRIPT_DIR}/../../operations/minio/cors.json"
  else
    MINIO_CORS_FILE="/app/cors.json"
  fi
fi

mc alias set local "http://${MINIO_ENDPOINT}" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
if mc mb --ignore-existing "local/${MINIO_BUCKET}"; then
  echo "minio: bucket ${MINIO_BUCKET} ready"
fi
if [ -f "${MINIO_CORS_FILE}" ]; then
  mc cors set "local/${MINIO_BUCKET}" "${MINIO_CORS_FILE}" || echo "minio: cors skipped (non-fatal)"
else
  echo "minio: cors skipped (missing ${MINIO_CORS_FILE})" >&2
fi
echo "minio: setup complete"
