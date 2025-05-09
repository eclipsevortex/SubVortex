#!/bin/bash

set -euo pipefail

### Phase 1: Initialization & Environment Setup

# Determine script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

source ../../scripts/tools.sh

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

# Load environment variables from .env safely
set -a
source .env
set +a

echo "🔧 Setting up $SERVICE_NAME..."

# Create checksum directory if it doesn't exist
mkdir -p "$CHECKSUM_DIR"

# Install Redis server if not already installed
install_redis_if_needed

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

### Phase 3: Data Preservation

if [[ "$REDIS_CHANGED" == true || "$CONF_CHANGED" == true ]]; then
    # echo "📤 Dumping Redis data..."
    # redis-cli SAVE || echo "⚠️ Could not save Redis data."
    
    echo "🛑 Stopping and disabling default redis-server systemd service..."
    sudo systemctl stop redis-server || true
    sudo systemctl disable redis-server || true
fi

### Phase 4: Configuration Deployment

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

# Update or remove Redis password in redis.conf based on SUBVORTEX_REDIS_PASSWORD
if [[ -v SUBVORTEX_REDIS_PASSWORD && -n "$SUBVORTEX_REDIS_PASSWORD" ]]; then
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
    if grep -qE '^\s*requirepass\s+' "$REDIS_CONF"; then
        echo "❌ Removing Redis password from redis.conf (SUBVORTEX_REDIS_PASSWORD is unset or empty)..."
        sudo sed -i '/^\s*requirepass\s\+/d' "$REDIS_CONF"
    else
        echo "⚠️ SUBVORTEX_REDIS_PASSWORD is unset or empty — no password configured in redis.conf."
    fi
fi

# Ensure Redis logs to stdout/stderr for PM2
echo "📄 Forcing logfile to stdout/stderr (logfile \"\")..."
if grep -qE '^\s*logfile\s+' "$REDIS_CONF"; then
    sudo sed -i 's|^\s*logfile\s\+.*|logfile ""|' "$REDIS_CONF"
elif grep -q "^# *logfile" "$REDIS_CONF"; then
    sudo sed -i '/^# *logfile/a logfile ""' "$REDIS_CONF"
else
    echo 'logfile ""' | sudo tee -a "$REDIS_CONF" > /dev/null
fi

### Phase 5: Systemd Unit Deployment

# Mask default redis-server systemd service
echo "🚫 Masking default redis-server systemd service..."
sudo systemctl mask redis-server || true

### Phase 6: Post-Deployment Verification

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
