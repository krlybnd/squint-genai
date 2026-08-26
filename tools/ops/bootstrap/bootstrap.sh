#!/usr/bin/env bash
# Post-start bootstrap: wait for infra, Alembic migrate, MinIO bucket + CORS.
set -euo pipefail

ROOT="/app"
ALEMBIC_INI="${ROOT}/alembic/alembic.ini"
CORS_FILE="${ROOT}/bootstrap/cors.json"

: "${DATABASE_URL:=postgresql+asyncpg://agentic:agentic@postgres:5432/agentic_rag_eval}"
: "${MINIO_ENDPOINT:=minio:9000}"
: "${MINIO_ACCESS_KEY:=minioadmin}"
: "${MINIO_SECRET_KEY:=minioadmin}"
: "${MINIO_BUCKET:=documents}"

WAIT_TIMEOUT="${WAIT_TIMEOUT:-180}"

fail() {
  echo "bootstrap failed: $*" >&2
  exit 1
}

postgres_url() {
  local url="$1"
  url="${url/postgresql+asyncpg/postgresql}"
  url="${url/postgresql+psycopg2/postgresql}"
  printf '%s' "$url"
}

wait_postgres() {
  local url elapsed=0
  url="$(postgres_url "$DATABASE_URL")"
  while (( elapsed < WAIT_TIMEOUT )); do
    if psql "$url" -c 'SELECT 1' >/dev/null 2>&1; then
      echo "postgres: ready"
      return 0
    fi
    echo "postgres: waiting..."
    sleep 2
    elapsed=$((elapsed + 2))
  done
  fail "postgres not ready"
}

wait_http() {
  local name="$1" url="$2" elapsed=0 code
  while (( elapsed < WAIT_TIMEOUT )); do
    code="$(curl -sf -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || echo "000")"
    if [[ "$code" != "000" && "$code" -lt 500 ]]; then
      echo "${name}: ready (${url})"
      return 0
    fi
    echo "${name}: waiting (${url})..."
    sleep 2
    elapsed=$((elapsed + 2))
  done
  fail "${name} not ready: ${url}"
}

wait_infra() {
  wait_postgres
  wait_http minio "http://${MINIO_ENDPOINT}/minio/health/live"
}

run_migrate() {
  echo "alembic: upgrade head"
  export DATABASE_URL
  (
    cd "${ROOT}/alembic"
    alembic upgrade head
  )
  echo "alembic: done"
}

setup_minio() {
  mc alias set local "http://${MINIO_ENDPOINT}" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
  if mc mb --ignore-existing "local/${MINIO_BUCKET}"; then
    echo "minio: bucket ${MINIO_BUCKET} ready"
  fi
  mc cors set "local/${MINIO_BUCKET}" "$CORS_FILE" || echo "minio: cors skipped (non-fatal)"
  echo "minio: setup complete"
}

main() {
  wait_infra
  run_migrate
  setup_minio
  echo "bootstrap complete"
}

main "$@"
