#!/bin/bash
set -euo pipefail

# Ensure script run as root
if [[ "$EUID" -ne 0 ]]; then
  echo "🛑 This script must be run as root. Re-running with sudo..."
  exec sudo "$0" "$@"
fi

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

NEURON_NAME="subvortex-validator"
SERVICE_NAME="$NEURON_NAME-redis"
CONFIG_DEST="/etc/redis"
REDIS_CONF="$CONFIG_DEST/redis.conf"
CHECKSUM_DIR="/var/tmp/dumps/redis/${SERVICE_NAME}-checksums"

echo "📦 Starting Validator Redis teardown for $SERVICE_NAME..."

# Stop and disable the systemd service if it exists
if systemctl list-units --type=service --all | grep -q "${SERVICE_NAME}.service"; then
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "🛑 Stopping systemd service: $SERVICE_NAME..."
        systemctl stop "${SERVICE_NAME}.service"
    fi
    
    echo "🚫 Disabling systemd service: $SERVICE_NAME..."
    systemctl disable "${SERVICE_NAME}.service" || true
    
    echo "🧹 Removing systemd service file..."
    rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
    
    echo "🔄 Reloading systemd daemon..."
    systemctl daemon-reexec
    systemctl daemon-reload
else
    echo "ℹ️ Systemd service ${SERVICE_NAME}.service not found. Skipping stop/disable."
fi

# Remove checksum directory
if [[ -d "$CHECKSUM_DIR" ]]; then
    echo "🧽 Removing checksum directory: $CHECKSUM_DIR"
    rm -rf "$CHECKSUM_DIR"
else
    echo "ℹ️ Checksum directory $CHECKSUM_DIR does not exist. Skipping."
fi

# Remove redis-server package if installed
echo "🔍 Checking if redis-server is installed..."
if dpkg -s redis-server >/dev/null 2>&1; then
    echo "🧼 Removing redis-server package..."
    apt purge -y redis-server
    apt autoremove -y
else
    echo "ℹ️ redis-server not installed. Nothing to remove."
fi

# --- System Unit Setup ---
echo "🚫 Unmasking default redis-server systemd service..."
systemctl unmask redis-server || true

echo "✅ Validator Redis teardown completed successfully."
