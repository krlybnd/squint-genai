FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv

COPY packages/shared packages/shared
COPY services/indexing services/indexing

WORKDIR /app/services/indexing
RUN uv sync --frozen --no-dev
# Docker/uv hardlinks identical NLTK files; NLTK pathsec refuses st_nlink>1.
RUN uv run python -c "from agentic_indexing.modules.pdf_indexing.pipeline import materialize_nltk_cache; materialize_nltk_cache()"

CMD ["uv", "run", "celery", "-A", "agentic_indexing.main:celery_app", "worker", "--loglevel=info", "--concurrency=2"]
