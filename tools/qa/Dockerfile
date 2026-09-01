# QA image: unit + API Gherkin + e2e + live eval. Host: docker compose --profile qa.
# Does not call Docker. Build context: repository root.
FROM mcr.microsoft.com/playwright:v1.52.0-noble

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        make \
        python3 \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    UV_PYTHON=python3 \
    QA_WORKSPACE=/workspace

WORKDIR /workspace

# One-shot: run the measuring gate, then exit (override: `run --rm qa make unittest`).
CMD ["make", "system-test"]
