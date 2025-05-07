#!/bin/bash

set -euo pipefail

SERVICE_NAME="subvortex-miner-neuron"

echo "🔍 Checking $SERVICE_NAME status..."

# Check if the service is active
if systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "🛑 $SERVICE_NAME is currently running — stopping it now..."
  sudo systemctl stop "$SERVICE_NAME"
  echo "✅ $SERVICE_NAME stopped successfully."
else
  echo "ℹ️ $SERVICE_NAME is not running. No action needed."
fi

echo "✅ Miner Neuron stopped successfully."