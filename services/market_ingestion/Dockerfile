# ==============================================================================
# Market Ingestion Microservice Dockerfile
# ==============================================================================
# Overview:
#   Builds the lightweight data collector service.
#
# Process:
#   1. Builder Stage: Installs dependencies (requests, pika, etc.).
#   2. Runtime Stage: Minimal runtime environment.
#   3. Security: Runs as non-root user.
# ==============================================================================

# --- Stage 1: Builder ---
FROM python:3.9-slim-bullseye AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies to a temporary location
COPY services/market_ingestion/requirements.txt /requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r /requirements.txt

# --- Stage 2: Runtime ---
FROM python:3.9-slim-bullseye

WORKDIR /app

# Install runtime dependencies (libpq is needed for psycopg2)
# We also create a non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 10000 appuser

# Copy installed python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY shared /app/shared
COPY services/market_ingestion /app/service

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Set environment
ENV PYTHONPATH="/app:/app/shared"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

WORKDIR /app/service/src

CMD ["python", "-u", "main.py"]
