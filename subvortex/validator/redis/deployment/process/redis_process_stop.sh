#!/bin/bash

set -euo pipefail

SERVICE_NAME="subvortex-validator-redis"

echo "🛑 Attempting to stop PM2 process: $SERVICE_NAME..."

# Check if PM2 process is running before stopping
if pm2 describe "$SERVICE_NAME" >/dev/null 2>&1; then
  echo "🔻 $SERVICE_NAME is currently running — stopping it now..."
  pm2 stop "$SERVICE_NAME"
else
  echo "ℹ️ $SERVICE_NAME is not running. No action needed."
fi

echo "✅ Validator Redis stopped successfully."
