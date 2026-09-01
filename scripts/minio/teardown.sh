#!/bin/sh
# Remove the MinIO bucket (objects included). start / setup-minio recreates it.
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

: "${MINIO_ENDPOINT:=minio:9000}"
: "${MINIO_ACCESS_KEY:=minioadmin}"
: "${MINIO_SECRET_KEY:=minioadmin}"
: "${MINIO_BUCKET:=documents}"

mc alias set local "http://${MINIO_ENDPOINT}" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
if mc rb --force "local/${MINIO_BUCKET}"; then
  echo "minio: bucket ${MINIO_BUCKET} removed"
else
  echo "minio: bucket ${MINIO_BUCKET} already absent"
fi
