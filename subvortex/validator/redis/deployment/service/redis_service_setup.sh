#!/bin/bash

set -euo pipefail

### Phase 1: Initialization & Environment Setup

# Determine script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Define constants and paths
NEURON_NAME=subvortex-validator
SERVICE_NAME="${NEURON_NAME}-redis"
DEPLOY_TEMPLATES="./deployment/templates"
SYSTEMD_DEST="/etc/systemd/system"
SYSTEMD_UNIT="${SYSTEMD_DEST}/${SERVICE_NAME}.service"
CHECKSUM_DIR="/var/tmp/subvortex.checksums/${SERVICE_NAME}-checksums"
REDIS_USER="redis"
REDIS_GROUP="redis"
REDIS_CONF="${SUBVORTEX_REDIS_CONFIG:-/etc/redis/redis.conf}"

echo "🔧 Setting up $SERVICE_NAME..."

# Load environment variables from .env safely
set -a
source .env
set +a

# Create checksum directory if it doesn't exist
mkdir -p "$CHECKSUM_DIR"

# Install Redis server if not already installed
echo "🚀 Installing Redis server if not already installed..."
if ! command -v redis-server >/dev/null; then
    sudo DEBIAN_FRONTEND=noninteractive apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -o Dpkg::Options::="--force-confold" redis-server
else
    echo "✅ redis-server already installed."
fi

### Phase 2: Checksum Verification

compute_checksum() {
    sha256sum "$1" | awk '{print $1}'
}

checksum_changed() {
    local file="$1"
    local name="$2"
    local new_hash
    new_hash=$(compute_checksum "$file")
    if [[ ! -f "$CHECKSUM_DIR/$name" ]] || [[ "$new_hash" != "$(cat "$CHECKSUM_DIR/$name")" ]]; then
        echo "$new_hash" > "$CHECKSUM_DIR/$name"
        return 0
    fi
    return 1
}

# Checksum redis binary
REDIS_BINARY="$(command -v redis-server)"
checksum_changed "$REDIS_BINARY" "redis-server.binary" && REDIS_CHANGED=true || REDIS_CHANGED=false

# Checksum redis config template
TEMPLATE_CONF="$DEPLOY_TEMPLATES/${SERVICE_NAME}.conf"
if [[ ! -f "$TEMPLATE_CONF" ]]; then
    echo "❌ Missing template: $TEMPLATE_CONF"
    exit 1
fi
checksum_changed "$TEMPLATE_CONF" "redis.conf.template" && CONF_CHANGED=true || CONF_CHANGED=false

# Checksum systemd service template
TEMPLATE_SERVICE="$DEPLOY_TEMPLATES/${SERVICE_NAME}.service"
if [[ ! -f "$TEMPLATE_SERVICE" ]]; then
    echo "❌ Missing template: $TEMPLATE_SERVICE"
    exit 1
fi
checksum_changed "$TEMPLATE_SERVICE" "systemd.unit.template" && UNIT_CHANGED=true || UNIT_CHANGED=false

### Phase 3: Pre-Deployment Checks

# Determine working Redis password
# determine_working_password() {
#     local env_pass conf_pass
    
#     env_pass="${SUBVORTEX_REDIS_PASSWORD:-}"
#     if [[ -f "$REDIS_CONF" ]]; then
#         conf_pass=$(grep -E '^\s*requirepass\s+' "$REDIS_CONF" | awk '{print $2}' || true)
#     else
#         conf_pass=""
#     fi
    
#     try_passwords=()
    
#     [[ -n "$env_pass" ]] && try_passwords+=("$env_pass")
#     [[ -n "$conf_pass" && "$conf_pass" != "$env_pass" ]] && try_passwords+=("$conf_pass")
    
#     for pass in "${try_passwords[@]}"; do
#         if redis-cli -a "$pass" PING 2>/dev/null | grep -q PONG; then
#             echo "$pass"
#             return 0
#         fi
#     done
    
#     # Try unauthenticated (empty password)
#     if redis-cli PING 2>/dev/null | grep -q PONG; then
#         echo ""
#         return 0
#     fi
    
#     return 1  # No working password
# }

# echo "🔍 Testing available Redis passwords..."
# if REDISCLI_AUTH="${SUBVORTEX_REDIS_PASSWORD:-}"; then
#     export REDISCLI_AUTH
#     if [[ -n "$REDISCLI_AUTH" ]]; then
#         echo "✅ Found working Redis password"
#     else
#         echo "✅ Redis allows unauthenticated access"
#     fi
# else
#     echo "❌ Failed to connect to Redis using provided or config password"
#     exit 1
# fi

### Phase 4: Data Preservation

if [[ "$REDIS_CHANGED" == true || "$CONF_CHANGED" == true ]]; then
    # echo "📤 Dumping Redis data..."
    # redis-cli SAVE || echo "⚠️ Could not save Redis data."
    
    echo "🛑 Stopping and disabling default redis-server systemd service..."
    sudo systemctl stop redis-server || true
    sudo systemctl disable redis-server || true
fi

### Phase 5: Configuration Deployment

# Prepare /etc/redis directory
echo "📂 Preparing redis directory..."
sudo mkdir -p "$(dirname "$REDIS_CONF")"
sudo chown "$REDIS_USER:$REDIS_GROUP" "$REDIS_CONF"

# Install updated redis.conf if changes are detected
if [[ "$REDIS_CHANGED" == true || "$CONF_CHANGED" == true ]]; then
    echo "📄 Installing updated redis.conf..."
    sudo cp "$TEMPLATE_CONF" "$REDIS_CONF"
    sudo chown "$REDIS_USER:$REDIS_GROUP" "$REDIS_CONF"
else
    echo "✅ No redis binary or config changes detected — skipping redis.conf update."
fi

# Update Redis password in redis.conf if necessary
if [[ -n "${SUBVORTEX_REDIS_PASSWORD:-}" ]]; then
    current_pass=$(grep -E '^\s*requirepass\s+' "$REDIS_CONF" | awk '{print $2}' || true)
    if [[ "$current_pass" != "$SUBVORTEX_REDIS_PASSWORD" ]]; then
        echo "🔐 Injecting or updating Redis password in redis.conf..."
        if grep -qE '^\s*requirepass\s+' "$REDIS_CONF"; then
            sudo sed -i "s|^\s*requirepass\s\+.*|requirepass $SUBVORTEX_REDIS_PASSWORD|" "$REDIS_CONF"
            elif grep -q "^# *requirepass" "$REDIS_CONF"; then
            sudo sed -i "/^# *requirepass/a requirepass $SUBVORTEX_REDIS_PASSWORD" "$REDIS_CONF"
        else
            echo "requirepass $SUBVORTEX_REDIS_PASSWORD" | sudo tee -a "$REDIS_CONF" > /dev/null
        fi
    else
        echo "🔐 Redis password already up-to-date — no changes made."
    fi
else
    echo "⚠️ Environment variable SUBVORTEX_REDIS_PASSWORD is not set — skipping password injection."
fi

# Parse log path from redis.conf
echo "📁 Parsing log path from redis.conf..."
log_path=$(grep -E '^\s*logfile\s+' "$REDIS_CONF" | awk '{print $2}')

# Prepare log directory if logfile is specified
if [[ -z "$log_path" || "$log_path" == '""' ]]; then
    echo "ℹ️ No logfile configured — Redis will log to stdout/stderr"
else
    log_dir=$(dirname "$log_path")
    echo "📁 Preparing log directory: $log_dir"
    sudo mkdir -p "$log_dir"
    sudo chown "$REDIS_USER:$REDIS_GROUP" "$log_dir"
    echo "✅ Log directory ready and owned by $REDIS_USER:$REDIS_GROUP"
fi

### Phase 6: Systemd Unit Deployment

# Mask default redis-server systemd service
echo "🚫 Masking default redis-server systemd service..."
sudo systemctl mask redis-server || true

# Install updated systemd unit file if changes are detected
if [[ "$UNIT_CHANGED" == true ]]; then
    echo "📄 Installing updated systemd unit file..."
    sudo cp "$TEMPLATE_SERVICE" "$SYSTEMD_UNIT"
else
    echo "✅ No systemd unit changes detected — skipping unit update."
fi

# Reload systemd daemon to apply changes
echo "🔧 Reloading systemd daemon..."
sudo systemctl daemon-reload

### Phase 7: Post-Deployment Verification

# Ensure Redis data directory exists and has correct permissions
REDIS_DATA_DIR=$(grep -E '^\s*dir\s+' "$REDIS_CONF" | awk '{print $2}')
if [[ -n "$REDIS_DATA_DIR" ]]; then
    echo "📁 Ensuring Redis data directory exists: $REDIS_DATA_DIR"
    sudo mkdir -p "$REDIS_DATA_DIR"
    sudo chown "$REDIS_USER:$REDIS_GROUP" "$REDIS_DATA_DIR"
else
    echo "⚠️ Could not determine Redis data directory from redis.conf."
fi

echo "✅ Validator Redis setup completed successfully."
