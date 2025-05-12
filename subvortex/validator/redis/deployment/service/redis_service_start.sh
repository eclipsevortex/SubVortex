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

SERVICE_NAME="subvortex-validator-redis"
SYSTEMD_DEST="/etc/systemd/system"
SYSTEMD_UNIT="$SYSTEMD_DEST/${SERVICE_NAME}.service"

echo "🚀 Starting $SERVICE_NAME..."

echo "🔧 Checking if $SERVICE_NAME is already enabled..."
if systemctl is-enabled "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "✅ $SERVICE_NAME is already enabled."
else
    if [[ -e "$SYSTEMD_UNIT" ]]; then
        echo "⚠️ Systemd unit file already exists at $SYSTEMD_UNIT — skipping enable to avoid conflict."
    else
        echo "🔧 Enabling $SERVICE_NAME to start on boot..."
        systemctl enable "$SERVICE_NAME"
    fi
fi

# Check if the service is already active
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "🔁 $SERVICE_NAME is already running — restarting it..."
    systemctl restart "$SERVICE_NAME"
else
    echo "▶️ $SERVICE_NAME is not running — starting it..."
    systemctl start "$SERVICE_NAME"
fi

# Final status check
echo "✅ Validator Redis started and is running."

