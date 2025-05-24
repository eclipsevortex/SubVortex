#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-neuron

# --- Basic Checks ---
if [[ "$EUID" -ne 0 ]]; then
  echo "🛑 Must be run as root. Re-running with sudo..."
  exec sudo "$0" "$@"
fi

echo "🛑 Stopping $SERVICE_NAME..."

# Stop the service
echo "🔍 Checking $SERVICE_NAME..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "🛑 $SERVICE_NAME is currently running — stopping it now..."
    systemctl stop "$SERVICE_NAME"
    echo "✅ $SERVICE_NAME stopped successfully."
else
    echo "ℹ️ $SERVICE_NAME is not running. No action needed."
fi

echo "✅ $SERVICE_NAME stopped successfully."