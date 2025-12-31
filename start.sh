#!/bin/bash

# Sentinel Quick Start Script
# Usage: ./start_project.sh

echo "🚀 Starting Sentinel AI Platform..."

# 1. Check for .env
if [ ! -f .env ]; then
    echo "❌ Error: .env file missing!"
    echo "   Please create a .env file with the required secrets."
    exit 1
fi

# 2. Start Docker Stack
echo "🐳 Launching Docker Containers..."
docker-compose up -d

echo "⏳ Waiting for services to stabilize (10s)..."
sleep 10

# 3. Initialize Vault (Secrets Injection)
echo "🔐 Initializing Security Vault..."
# Export env vars from .env for the script to use
export $(grep -v '^#' .env | xargs)

# Set Vault Address for Local Script execution
export VAULT_ADDR='http://localhost:8200'
export VAULT_TOKEN='root_token' # Dev mode token

if [ -f services/vault_init.sh ]; then
    sh services/vault_init.sh
else
    echo "⚠️ Warning: services/vault_init.sh not found. Vault might be uninitialized."
fi

echo "✅ Project IS LIVE!"
echo "   - Dashboard: http://localhost:3000"
echo "   - RabbitMQ:  http://localhost:15672 (admin/passme123)"
echo "   - API Docs:  Check SENTINEL_DOCUMENTATION.md"
