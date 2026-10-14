# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

LABEL org.opencontainers.image.title="cadence" \
      org.opencontainers.image.description="Cadence speech-delivery coach: Gradio dashboard, coach web app and FastAPI scoring API" \
      org.opencontainers.image.source="https://github.com/kanakamurthyh/Cadence"

# ffmpeg for audio decoding (soundfile wheels bundle libsndfile, so it is not installed separately)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=0 \
    OMP_NUM_THREADS=2

WORKDIR /app

# Dependencies first (cached layer), project second. No dev group, no extras.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Non-root runtime user. Only the HF cache is made writable (no chown -R of the
# multi-GB venv, which would duplicate the layer). Mount a volume on the cache.
RUN useradd --create-home --uid 1000 cadence \
    && mkdir -p /app/.cache/huggingface \
    && chown -R cadence:cadence /app/.cache
ENV HF_HOME=/app/.cache/huggingface \
    PATH="/app/.venv/bin:$PATH" \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860
USER cadence

EXPOSE 7860 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://localhost:7860/', timeout=4); sys.exit(0)" || exit 1

CMD ["/app/.venv/bin/cadence", "app"]
