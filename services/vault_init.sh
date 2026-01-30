#!/bin/sh

# Wait for Vault to be ready
echo "⏳ Waiting for Vault to be online..."
until curl -s $VAULT_ADDR/v1/sys/health > /dev/null; do
    sleep 1
done
echo "✅ Vault is online at $VAULT_ADDR"

# --- 1. Initialize & Unseal ---
# Check if initialized
INIT_STATUS=$(curl -s $VAULT_ADDR/v1/sys/init | grep '"initialized":true')

if [ -z "$INIT_STATUS" ]; then
    echo "⚙️  Initializing Vault..."
    # Initialize with 1 key share for simplicity in this 'simulated prod' env
    # In real prod, use 5 shares, 3 threshold.
    curl -s --request POST --data '{"secret_shares": 1, "secret_threshold": 1}' $VAULT_ADDR/v1/sys/init > /tmp/vault_init.json
    
    # Extract Keys and Token
    # Extract Keys and Token using sed for robustness (since jq might be missing)
    UNSEAL_KEY=$(cat /tmp/vault_init.json | sed -n 's/.*"keys_base64":\["\([^"]*\)".*/\1/p')
    ROOT_TOKEN=$(cat /tmp/vault_init.json | sed -n 's/.*"root_token":"\([^"]*\)".*/\1/p')
    
    echo "🔑 Vault Initialized."
    echo "    Unseal Key: $UNSEAL_KEY"
    echo "    Root Token: $ROOT_TOKEN"
    
    # Save keys persistently (SECURE THIS FILE IN REAL PROD)
    mkdir -p /vault/file/keys
    echo $UNSEAL_KEY > /vault/file/keys/unseal_key
    echo $ROOT_TOKEN > /vault/file/keys/root_token
else
    echo "ℹ️  Vault already initialized."
    UNSEAL_KEY=$(cat /vault/file/keys/unseal_key)
    ROOT_TOKEN=$(cat /vault/file/keys/root_token)
fi

# Unseal
echo "🔓 Unsealing Vault..."
curl -s --request POST --data "{\"key\": \"$UNSEAL_KEY\"}" $VAULT_ADDR/v1/sys/unseal > /dev/null

# Log in
export VAULT_TOKEN=$ROOT_TOKEN

# --- 2. Enable Key-Value Engine (if not exists) ---
# Note: HashiCorp Vault dev mode enables 'secret' v2 by default. 
# In PROD server mode, we might need to enable it.
MOUNT_CHECK=$(curl -s --header "X-Vault-Token: $VAULT_TOKEN" $VAULT_ADDR/v1/sys/mounts | grep '"secret/":')
if [ -z "$MOUNT_CHECK" ]; then
    echo "📂 Enabling KV secrets engine at 'secret/'..."
    curl -s --header "X-Vault-Token: $VAULT_TOKEN" \
        --request POST \
        --data '{"type": "kv-v2"}' \
        $VAULT_ADDR/v1/sys/mounts/secret
fi

# --- 3. Setup AppRole Auth ---
echo "🛡️  Configuring AppRole Authentication..."
curl -s --header "X-Vault-Token: $VAULT_TOKEN" \
    --request POST \
    --data '{"type": "approle"}' \
    $VAULT_ADDR/v1/sys/auth/approle > /dev/null

# Create Policy (Read Only for Sentinel)
echo 'path "secret/data/sentinel" { capabilities = ["read"] }' > /tmp/sentinel_policy.hcl
curl -s --header "X-Vault-Token: $VAULT_TOKEN" \
    --request PUT \
    --data "{\"policy\": \"path \\\"secret/data/sentinel\\\" { capabilities = [\\\"read\\\"] }\"}" \
    $VAULT_ADDR/v1/sys/policy/sentinel-policy

# Create AppRole 'sentinel-role' linked to policy
curl -s --header "X-Vault-Token: $VAULT_TOKEN" \
    --request POST \
    --data '{"token_policies": "sentinel-policy", "token_ttl": "1h", "token_max_ttl": "4h"}' \
    $VAULT_ADDR/v1/auth/approle/role/sentinel-role

# Get RoleID
ROLE_ID=$(curl -s --header "X-Vault-Token: $VAULT_TOKEN" $VAULT_ADDR/v1/auth/approle/role/sentinel-role/role-id | sed -n 's/.*"role_id":"\([^"]*\)".*/\1/p')

# Generate SecretID
SECRET_ID=$(curl -s --header "X-Vault-Token: $VAULT_TOKEN" --request POST $VAULT_ADDR/v1/auth/approle/role/sentinel-role/secret-id | sed -n 's/.*"secret_id":"\([^"]*\)".*/\1/p')

echo "🎫 AppRole Credentials Generated:"
echo "    Role ID: $ROLE_ID"
echo "    Secret ID: $SECRET_ID"

# Save to shared volume for apps to pick up (Simulating Secure Injection)
echo $ROLE_ID > /vault/file/keys/role_id
echo $SECRET_ID > /vault/file/keys/secret_id

# --- 4. Inject Secrets ---
write_secret() {
    key=$1
    val=$2
    if [ -z "$val" ]; then
        echo "⚠️  Skipping $key (Empty)"
    else
        # KV v2 Write
        curl -s --header "X-Vault-Token: $VAULT_TOKEN" \
            --request POST \
            --data "{\"data\": {\"$key\": \"$val\"}}" \
            $VAULT_ADDR/v1/secret/data/sentinel > /dev/null 
            # Note: This overwrites the whole path if not careful with patches. 
            # Since we write 1-by-1, subsequent writes disable previous if we don't merge.
            # FIX: Write ALL at once.
    fi
}

echo "🚀 Injecting Application Secrets..."

# Construct JSON payload for generic write
# Using jq or manual string building. 
JSON_PAYLOAD="{\"data\": {"
JSON_PAYLOAD="$JSON_PAYLOAD \"FRED_API_KEY\": \"$FRED_API_KEY\","
JSON_PAYLOAD="$JSON_PAYLOAD \"EIA_API_KEY\": \"$EIA_API_KEY\","
JSON_PAYLOAD="$JSON_PAYLOAD \"COMTRADE_API_KEY\": \"$COMTRADE_API_KEY\","
JSON_PAYLOAD="$JSON_PAYLOAD \"RABBITMQ_USER\": \"$RABBITMQ_USER\","
JSON_PAYLOAD="$JSON_PAYLOAD \"RABBITMQ_PASS\": \"$RABBITMQ_PASS\","
JSON_PAYLOAD="$JSON_PAYLOAD \"DB_PASSWORD\": \"$DB_PASSWORD\""
JSON_PAYLOAD="$JSON_PAYLOAD }}"

curl -s --header "X-Vault-Token: $VAULT_TOKEN" \
    --request POST \
    --data "$JSON_PAYLOAD" \
    $VAULT_ADDR/v1/secret/data/sentinel > /dev/null

echo "✨ Vault Initialization Complete."
# Keep container alive to hold the keys/volume if needed, or exit successfully.
# Exit allows compose to see it 'completed' but we want the volume to persist.

