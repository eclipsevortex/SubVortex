#!/bin/bash
w
set -euo pipefail

SERVICE_NAME=subvortex-validator-redis
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

echo "🧹 Starting $SERVICE_NAME teardown..."

# Fallback to script location if PROJECT_WORKING_DIR is not set
if [[ -z "$PROJECT_WORKING_DIR" ]]; then
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_WORKING_DIR="$(realpath "$SCRIPT_PATH/../../../../../")"
  echo "📁 PROJECT_WORKING_DIR not set — using fallback: $PROJECT_WORKING_DIR"
else
  echo "📁 Using PROJECT_WORKING_DIR from environment: $PROJECT_WORKING_DIR"
fi

SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/validator/redis"

# Stop and delete the PM2 process
echo "🔍 Checking $SERVICE_NAME..."
if pm2 describe "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "🛑 Stopping process $SERVICE_NAME..."
    pm2 stop "$SERVICE_NAME"
    
    echo "🗑️ Deleting process $SERVICE_NAME..."
    pm2 delete "$SERVICE_NAME"
else
    echo "ℹ️ Process $SERVICE_NAME not found. Skipping stop/delete."
fi

# --- Package service cleanup ---
echo "📦 Removing package 'redis-server'..."

if command -v apt-get &> /dev/null; then
    sudo apt-get purge -y redis-server
    sudo apt-get autoremove -y
elif command -v dnf &> /dev/null; then
    sudo dnf remove -y redis-server
elif command -v pacman &> /dev/null; then
    sudo pacman -Rns --noconfirm redis-server
else
    echo "⚠️ Unsupported package manager. Please uninstall redis-server manually."
fi


echo "✅ $SERVICE_NAME uninstalled successfully."