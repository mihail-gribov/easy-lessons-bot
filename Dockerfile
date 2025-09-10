# Dockerfile for Easy Lessons Bot (MVP)
# Base image: Python 3.12 slim

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# System deps (minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv (user-local)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -s /root/.local/bin/uv /usr/local/bin/uv

# Copy dependency manifests first (for better caching)
COPY pyproject.toml ./
COPY uv.lock* ./

# Install project dependencies into a local virtualenv at /app/.venv
RUN uv sync --frozen --no-dev \
    && find /root/.cache -type f -delete || true

# Make venv active by default for subsequent layers and runtime
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source
COPY app/ app/
COPY bot/ bot/
COPY core/ core/
COPY settings/ settings/
COPY Makefile Makefile

# Create non-root user and log directory
RUN adduser --disabled-password --gecos '' appuser \
    && mkdir -p /log \
    && chown -R appuser:appuser /app /log

USER appuser

# Default command runs the bot
CMD ["python", "-m", "app.main"]


