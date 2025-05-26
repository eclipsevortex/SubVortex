#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-metagraph

# --- Basic Checks ---
if [[ "$EUID" -ne 0 ]]; then
  echo "🛑 Must be run as root. Re-running with sudo..."
  exec sudo "$0" "$@"
fi

echo "🚀 Starting $SERVICE_NAME..."

# Start or restart the service
echo "🔍 Checking $SERVICE_NAME..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "🔁 $SERVICE_NAME is already running — restarting..."
    systemctl restart "$SERVICE_NAME"
else
    echo "🚀 Starting $SERVICE_NAME for the first time..."
    systemctl start "$SERVICE_NAME"
fi

echo "✅ $SERVICE_NAME started successfully."