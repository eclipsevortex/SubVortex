#!/bin/bash

set -euo pipefail

SERVICE_NAME="subvortex-validator-redis"

echo "🚀 Starting $SERVICE_NAME..."

sudo systemctl enable "$SERVICE_NAME" >/dev/null 2>&1

# Check if the service is already active
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "🔁 $SERVICE_NAME is already running — restarting it..."
    sudo systemctl restart "$SERVICE_NAME"
else
    echo "▶️ $SERVICE_NAME is not running — starting it..."
    sudo systemctl start "$SERVICE_NAME"
fi

# Final status check
sleep 1  # short wait for startup
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Validator Redis started and is running."
else
    echo "❌ Failed to start $SERVICE_NAME. Run 'journalctl -u $SERVICE_NAME -xe' for details."
    exit 1
fi

