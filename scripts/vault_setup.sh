#!/bin/bash

# scripts/vault_setup.sh
# Starts Vault and injects secrets from .env

# 1. Start Vault Service
echo "🚀 Starting Vault Container..."
docker-compose up -d vault

echo "⏳ Waiting for Vault to initialize..."
# Simple wait loop
until curl -s http://localhost:8200/v1/sys/health > /dev/null; do
    echo "   ...waiting for health check (http://localhost:8200)..."
    sleep 2
done
echo "✅ Vault is UP."

# 2. Read .env file
# Export all variables from .env to the current shell
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else 
  echo "⚠️ .env file not found!"
  exit 1
fi

# 3. Construct JSON Payload
# Create a JSON object with the keys the application expects
# Note: We use 'jq' if available, otherwise manual string construction. 
# For portability, we'll try a python one-liner or simple string if jq is missing.

# Basic check for critical keys
echo "🔑 Preparing Secrets for Injection..."

# Construct JSON string safely using Python (installed on mac)
# We map the ENV vars to the keys Vault expects
JSON_PAYLOAD=$(python3 -c "import os, json; print(json.dumps({
    'data': {
        'YAHOO_API_KEY': os.environ.get('YAHOO_API_KEY', ''),
        'FRED_API_KEY': os.environ.get('FRED_API_KEY', ''),
        'COMTRADE_API_KEY': os.environ.get('COMTRADE_API_KEY', ''),
        'EIA_API_KEY': os.environ.get('EIA_API_KEY', ''),
        'RABBITMQ_USER': os.environ.get('RABBITMQ_USER', 'admin'),
        'RABBITMQ_PASS': os.environ.get('RABBITMQ_PASS', 'passme123'),
        'DB_PASSWORD': os.environ.get('DB_PASSWORD', 'passme123')
    }
}))")

# 4. Inject Secrets (KV v2 path: secret/data/sentinel)
# Token is 'root_token' from docker-compose environment `VAULT_DEV_ROOT_TOKEN_ID`
echo "💉 Injecting Secrets into Vault (secret/data/sentinel)..."

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  --header "X-Vault-Token: root_token" \
  --request POST \
  --data "$JSON_PAYLOAD" \
  http://localhost:8200/v1/secret/data/sentinel)

if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 204 ]; then
    echo "✅ Secrets Injected Successfully."
else
    echo "❌ Failed to inject secrets. HTTP Code: $HTTP_CODE"
    exit 1
fi
