# -- Stage 1: Build & Dependencies --
FROM python:3.13-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install system dependencies for weasyprint and soundfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libffi-dev \
    shared-mime-info \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtualenv
RUN uv sync --frozen --no-dev

# -- Stage 2: Runtime --
FROM python:3.13-slim

WORKDIR /app

# Copy system libraries from builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv and app from builder
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Use shell form to allow environment variable expansion ($PORT)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
