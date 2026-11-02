# Small official Python image; the version matches backend/.python-version
FROM python:3.13-slim

# Copy the uv binary from its official image instead of installing it with pip
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv

WORKDIR /app

# Compile .pyc files at build time (faster startup); copy files instead of linking from the cache
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    HF_HOME=/app/.cache/huggingface \
    PATH="/app/.venv/bin:$PATH"

# Dependencies first: this layer is only rebuilt when the lock file changes, not on every code edit
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

# App code last, because it changes most often
COPY app ./app

# Run as an unprivileged user; the folders that become volumes must belong to that user
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p data .cache/huggingface \
    && chown -R appuser:appuser data .cache
USER appuser

EXPOSE 8000
# 0.0.0.0, not localhost: inside a container, localhost is unreachable from outside it
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
