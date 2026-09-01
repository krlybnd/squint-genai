# Operator image: `make initialization` (infra) then `make bootstrap` (after apps), then idle.
# Host entry is Docker Compose / `docker compose exec ops make …` — not tests.
# Build context: repository root.
FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        curl \
        jq \
        make \
        postgresql-client \
        redis-tools \
    && rm -rf /var/lib/apt/lists/*

COPY --from=minio/mc:latest /usr/bin/mc /usr/bin/mc

WORKDIR /app

RUN pip install --no-cache-dir \
    alembic \
    psycopg2-binary \
    sqlalchemy \
    pydantic \
    pydantic-settings

COPY scripts/minio/ /app/scripts/minio/
COPY scripts/postgres/ /app/scripts/postgres/
COPY operations/minio/cors.json /app/cors.json
COPY packages/shared/src/ /app/packages/shared/src/
COPY packages/shared/alembic/ /app/alembic/
COPY locales/messages/ /app/locales/messages/

ENV OPS_WORKSPACE=/workspace

RUN chmod +x /app/scripts/minio/*.sh /app/scripts/postgres/*.sh

CMD ["bash", "-c", "make -C ${OPS_WORKSPACE:-/workspace} initialization && make -C ${OPS_WORKSPACE:-/workspace} bootstrap && touch /tmp/ops-ready && exec sleep infinity"]
