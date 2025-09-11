# Dockerfile for Easy Lessons Bot (MVP)
# Multi-stage build for optimized production image

# Build stage
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install system dependencies for building
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -s /root/.local/bin/uv /usr/local/bin/uv

# Copy dependency manifests first (for better caching)
COPY pyproject.toml uv.lock* ./

# Install project dependencies into a local virtualenv at /app/.venv
RUN uv sync --frozen --no-dev \
    && find /root/.cache -type f -delete || true

# Runtime stage
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application source code
COPY app/ app/
COPY bot/ bot/
COPY core/ core/
COPY settings/ settings/

# Create non-root user and log directory
RUN adduser --disabled-password --gecos '' appuser \
    && mkdir -p /log \
    && chown -R appuser:appuser /app /log

USER appuser

# Health check to monitor bot status
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command runs the bot
CMD ["python", "-m", "app.main"]


