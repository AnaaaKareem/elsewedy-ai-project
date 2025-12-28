FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (needed for psycopg2)
RUN apt-get update && apt-get install -y libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy common logic
COPY shared /app/shared

# Copy service code
COPY services/market_ingestion /app/service

# Set python path to include shared directory
ENV PYTHONPATH="/app/shared"

# Install dependencies
COPY services/market_ingestion/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --prefer-binary -r /app/requirements.txt

WORKDIR /app/service/src

CMD ["python", "-u", "main.py"]
