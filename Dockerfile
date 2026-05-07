FROM python:3.11-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    CHROMA_PATH=/app/chroma \
    EMBED_CACHE_DIR=/app/.cache/embeddings \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev --no-group eval

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev --no-group eval

EXPOSE 8000

CMD ["python", "scripts/start_server.py"]
