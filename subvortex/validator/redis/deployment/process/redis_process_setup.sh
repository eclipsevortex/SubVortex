#!/bin/bash

set -euo pipefail

# Determine working directory: prefer SUBVORTEX_WORKING_DIR, fallback to script location
SCRIPT_DIR="$(cd "$(dirname "$(python3 -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$0")")" && pwd)"

# Find project root by walking up until LICENSE is found
find_project_root() {
    local dir="$1"
    while [[ "$dir" != "/" ]]; do
        [[ -f "$dir/LICENSE" ]] && { echo "$dir"; return; }
        dir="$(dirname "$dir")"
    done
    return 1
}

PROJECT_ROOT="$(find_project_root "$SCRIPT_DIR")" || {
    echo "❌ Could not detect project root (LICENSE not found)"
    exit 1
}

# Resolve final working directory
if [[ -n "${SUBVORTEX_WORKING_DIR:-}" ]]; then
    REL_PATH="${SCRIPT_DIR#$PROJECT_ROOT/}"
    TARGET_DIR="$SUBVORTEX_WORKING_DIR/$REL_PATH"
    [[ -d "$TARGET_DIR" ]] || { echo "❌ Target directory does not exist: $TARGET_DIR"; exit 1; }
    echo "📁 Using SUBVORTEX_WORKING_DIR: $TARGET_DIR"
    cd "$TARGET_DIR/../.."
else
    echo "📁 Using fallback PROJECT_ROOT: $SCRIPT_DIR"
    cd "$SCRIPT_DIR/../.."
fi

echo "📍 Working directory: $(pwd)"

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
install_specific_redis

## Stop default redis-server
echo "🛑 Stopping and disabling default redis-server systemd service..."
sudo systemctl stop redis-server || true
sudo systemctl disable redis-server || true

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

# Ensure Redis logs to stdout/stderr for PM2
echo "📄 Forcing logfile to stdout/stderr (logfile \"\")..."
if grep -qE '^\s*logfile\s+' "$REDIS_CONF"; then
    sudo sed -i 's|^\s*logfile\s\+.*|logfile ""|' "$REDIS_CONF"
elif grep -q "^# *logfile" "$REDIS_CONF"; then
    sudo sed -i '/^# *logfile/a logfile ""' "$REDIS_CONF"
else
    echo 'logfile ""' | sudo tee -a "$REDIS_CONF" > /dev/null
fi

# Mask default redis-server systemd service
echo "🚫 Masking default redis-server systemd service..."
sudo systemctl mask redis-server || true

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
