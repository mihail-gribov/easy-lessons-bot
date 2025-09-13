# Dockerfile for Easy Lessons Bot (MVP)
# Multi-stage build for optimized production image

# Build arguments for version metadata
ARG VERSION=unknown
ARG GIT_COMMIT=unknown
ARG BUILD_DATE=unknown

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

# Re-declare build args for runtime stage
ARG VERSION=unknown
ARG GIT_COMMIT=unknown
ARG BUILD_DATE=unknown

# Set environment variables from build args
ENV VERSION=$VERSION
ENV GIT_COMMIT=$GIT_COMMIT
ENV BUILD_DATE=$BUILD_DATE

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
COPY scripts/ scripts/

# Create non-root user, log directory, and data directory
RUN adduser --disabled-password --gecos '' appuser \
    && mkdir -p /log /app/data \
    && chown -R appuser:appuser /app /log

USER appuser

# Add version metadata as labels
LABEL org.opencontainers.image.title="Easy Lessons Bot" \
      org.opencontainers.image.description="Telegram bot for easy learning with LLM" \
      org.opencontainers.image.version="$VERSION" \
      org.opencontainers.image.revision="$GIT_COMMIT" \
      org.opencontainers.image.created="$BUILD_DATE" \
      org.opencontainers.image.source="https://github.com/your-org/easy-lessons-bot" \
      org.opencontainers.image.vendor="Easy Lessons Bot Team"

# Health check to monitor bot status
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python scripts/health_check.py || exit 1

# Default command runs the bot
CMD ["python", "-m", "app.main"]


