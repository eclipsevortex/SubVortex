#!/bin/bash

set -e

SERVICE_NAME="subvortex-miner"

echo "🔍 Checking $SERVICE_NAME status..."

if systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "🛑 Stopping $SERVICE_NAME"
  sudo systemctl stop "$SERVICE_NAME"
else
  echo "ℹ️ $SERVICE_NAME is not running"
fi
