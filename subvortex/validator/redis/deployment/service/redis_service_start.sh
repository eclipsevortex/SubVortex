#!/bin/bash

set -euo pipefail

# Ensure script run as root
if [[ "$EUID" -ne 0 ]]; then
  echo "🛑 This script must be run as root. Re-running with sudo..."
  exec sudo "$0" "$@"
fi

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

