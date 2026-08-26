FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv

COPY packages/shared packages/shared
COPY services/chat services/chat

WORKDIR /app/services/chat
RUN uv sync --frozen --no-dev

EXPOSE 8002
CMD ["uv", "run", "uvicorn", "agentic_chat.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8002"]
