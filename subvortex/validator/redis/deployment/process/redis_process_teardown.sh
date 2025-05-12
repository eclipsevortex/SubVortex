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
    cd "$TARGET_DIR"
else
    echo "📁 Using fallback PROJECT_ROOT: $SCRIPT_DIR"
    cd "$SCRIPT_DIR"
fi

echo "📍 Working directory: $(pwd)"

NEURON_NAME="subvortex-validator"
SERVICE_NAME="$NEURON_NAME-redis"
CONFIG_DEST="/etc/redis"
REDIS_CONF="$CONFIG_DEST/redis.conf"
LOG_DIR="/var/log/$SERVICE_NAME"
CHECKSUM_DIR="/var/tmp/dumps/redis/${SERVICE_NAME}-checksums"

echo "📦 Starting Validator Redis teardown for PM2 setup..."

# Stop and delete PM2 process if running
echo "🛑 Stopping and deleting PM2 process if it exists..."
if pm2 describe "$SERVICE_NAME" >/dev/null 2>&1; then
    pm2 stop "$SERVICE_NAME" || true
    pm2 delete "$SERVICE_NAME" || true
    echo "✅ PM2 process $SERVICE_NAME removed."
else
    echo "ℹ️ No PM2 process found for $SERVICE_NAME."
fi

# Remove checksum directory
if [[ -d "$CHECKSUM_DIR" ]]; then
    echo "🧽 Removing checksum directory: $CHECKSUM_DIR"
    sudo rm -rf "$CHECKSUM_DIR"
else
    echo "ℹ️ Checksum directory $CHECKSUM_DIR does not exist. Skipping."
fi

# Uninstall redis-server if installed
echo "🔍 Checking if redis-server is installed..."
if command -v redis-server >/dev/null 2>&1; then
    echo "🧨 redis-server is installed. Uninstalling..."
    sudo apt purge -y redis-server
    sudo apt autoremove -y
    echo "✅ redis-server uninstalled."
else
    echo "ℹ️ redis-server not installed — nothing to uninstall."
fi

# --- System Unit Setup ---
echo "🚫 Unmasking default redis-server systemd service..."
sudo systemctl unmask redis-server || true

echo "✅ Validator Redis teardown completed successfully."