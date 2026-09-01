#!/bin/sh
# Alembic upgrade head. Prefers workspace copy; falls back to /app in the ops image.
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT="${OPS_WORKSPACE:-${SCRIPT_DIR}/../..}"

if [ -d "${ROOT}/packages/shared/alembic" ]; then
  ALEMBIC_DIR="${ROOT}/packages/shared/alembic"
  PYTHONPATH="${ROOT}/packages/shared/src"
else
  ALEMBIC_DIR="/app/alembic"
  PYTHONPATH="/app/packages/shared/src"
fi

export DATABASE_URL PYTHONPATH
echo "alembic: upgrade head (${ALEMBIC_DIR})"
if command -v alembic >/dev/null 2>&1; then
  (
    cd "${ALEMBIC_DIR}"
    alembic upgrade head
  )
else
  cd "${ROOT}/packages/shared"
  uv run alembic -c alembic/alembic.ini upgrade head
fi
echo "alembic: done"
