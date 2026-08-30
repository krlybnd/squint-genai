FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv

COPY locales locales
COPY packages/shared packages/shared
COPY packages/generated/keycloak-admin-client packages/generated/keycloak-admin-client
COPY services/admin services/admin

WORKDIR /app/services/admin
RUN uv sync --frozen --no-dev

EXPOSE 8003
CMD ["uv", "run", "uvicorn", "agentic_admin.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8003"]
