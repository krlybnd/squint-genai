# Lightweight post-start bootstrap: Alembic + MinIO setup.
# Build context: repository root (see docker-compose / Dagger Image).
FROM python:3.12-alpine

RUN apk add --no-cache bash curl postgresql-client

COPY --from=minio/mc:latest /usr/bin/mc /usr/bin/mc

WORKDIR /app

COPY tools/ops/bootstrap/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY tools/ops/bootstrap/ /app/bootstrap/
COPY packages/shared/src/ /app/packages/shared/src/
COPY packages/shared/alembic/ /app/alembic/

ENV PYTHONPATH=/app/packages/shared/src

RUN chmod +x /app/bootstrap/bootstrap.sh

ENTRYPOINT ["/app/bootstrap/bootstrap.sh"]
