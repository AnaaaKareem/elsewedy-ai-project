# ==============================================================================
# AI Engine Microservice Dockerfile
# ==============================================================================
# Overview:
#   Builds the Python environment for the AI Engine, including heavy dependencies
#   like PyTorch, XGBoost, and SciPy.
#
# Process:
#   1. Builder Stage: Compiles dependencies and wheels (reducing final image size).
#   2. Runtime Stage: Copies compiled packages and application code.
#   3. Security: Runs as a non-root user ('appuser') for production safety.
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
COPY services/ai_engine/requirements.txt /requirements.txt
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
COPY services/ai_engine /app/service

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Set environment
ENV PYTHONPATH="/app:/app/shared"
# Disallow writing bytecode to keep image clean (optional but good for prod)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

WORKDIR /app/service/src

CMD ["python", "-u", "main.py"]
