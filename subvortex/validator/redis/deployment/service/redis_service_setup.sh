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
SYSTEMD_DEST="/etc/systemd/user"
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

### Phase 3: Data Preservation
echo "🛑 Stopping and disabling default redis-server systemd service..."
sudo systemctl stop redis-server || true
sudo systemctl disable redis-server || true

### Phase 4: Configuration Deployment

# Prepare /etc/redis directory
echo "📂 Preparing redis directory..."
sudo mkdir -p "$(dirname "$REDIS_CONF")"
sudo chown "$REDIS_USER:$REDIS_GROUP" "$REDIS_CONF"

# Install updated redis.conf if changes are detected
echo "📄 Installing updated redis.conf..."
TEMPLATE_CONF="$DEPLOY_TEMPLATES/${SERVICE_NAME}.conf"
sudo cp "$TEMPLATE_CONF" "$REDIS_CONF"
sudo chown "$REDIS_USER:$REDIS_GROUP" "$REDIS_CONF"

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

### Phase 5: Systemd Unit Deployment

# Mask default redis-server systemd service
echo "🚫 Masking default redis-server systemd service..."
sudo systemctl mask redis-server || true

# Install updated systemd unit file if changes are detected
echo "📄 Installing updated systemd unit file..."
TEMPLATE_SERVICE="$DEPLOY_TEMPLATES/${SERVICE_NAME}.service"
sudo cp "$TEMPLATE_SERVICE" "$SYSTEMD_UNIT"

# Reload systemd daemon to apply changes
echo "🔧 Reloading systemd daemon..."
sudo systemctl daemon-reload

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
