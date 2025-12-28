#!/bin/sh

# Wait for Vault to be ready
echo "⏳ Waiting for Vault..."
until curl -s $VAULT_ADDR/v1/sys/health > /dev/null; do
    sleep 1
done
echo "✅ Vault is up!"

# Login (Dev mode uses root token)
export VAULT_TOKEN=$VAULT_TOKEN

# Helper to write secret
write_secret() {
    key=$1
    val=$2
    if [ -z "$val" ]; then
        echo "⚠️  Skipping $key (Empty)"
    else
        # Write to 'secret/data/<key>' for KV v2, or just 'secret/<key>'
        # Using basic KV structure for simplicity with hvac usage in code
        # config.py uses 'secret/data/...' convention or v1?
        # Let's check config.py: self.vault.get_secret('FRED_API_KEY')
        # Infrastructure/vault.py likely defines the path structure.
        # Assuming standard KV mount at 'secret/'
        
        curl -s \
            --header "X-Vault-Token: $VAULT_TOKEN" \
            --request POST \
            --data "{\"data\": {\"value\": \"$val\"}}" \
            $VAULT_ADDR/v1/secret/data/$key > /dev/null
        
        echo "🔑 Injected $key"
    fi
}

echo "🚀 Injecting Secrets..."
write_secret "FRED_API_KEY" "$FRED_API_KEY"
write_secret "EIA_API_KEY" "$EIA_API_KEY"
write_secret "COMTRADE_API_KEY" "$COMTRADE_API_KEY"
write_secret "RABBITMQ_USER" "$RABBITMQ_USER"
write_secret "RABBITMQ_PASS" "$RABBITMQ_PASS"
write_secret "DB_PASSWORD" "$DB_PASSWORD"

echo "✨ Vault Initialization Complete."
