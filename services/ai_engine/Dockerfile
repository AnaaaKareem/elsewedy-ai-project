FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy common logic
COPY shared /app/shared

# Copy service code
COPY services/ai_engine /app/service

# Set python path to include shared directory
# Note: 'ai_models' is now local in /app/service/src, so it's transparently importable
ENV PYTHONPATH="/app/shared"

# Install dependencies
COPY services/ai_engine/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --prefer-binary -r /app/requirements.txt

WORKDIR /app/service/src

CMD ["python", "-u", "main.py"]
