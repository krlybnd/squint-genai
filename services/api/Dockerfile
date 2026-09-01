FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv

COPY locales locales
COPY packages/shared packages/shared
COPY packages/generated/keycloak-admin-client packages/generated/keycloak-admin-client
COPY services/api services/api

WORKDIR /app/services/api
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "agentic_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
