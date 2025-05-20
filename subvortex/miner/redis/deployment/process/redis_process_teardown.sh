#!/bin/bash
w
set -euo pipefail

SERVICE_NAME=subvortex-miner-redis
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

PROJECT_EXECUTION_DIR="${SUBVORTEX_EXECUTION_DIR:-$PROJECT_WORKING_DIR}"
SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/miner/redis"

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
echo "🧹 Running provision uninstall hook..."
bash "$SERVICE_WORKING_DIR/deployment/provision/redis_server_uninstall.sh"


echo "✅ $SERVICE_NAME uninstalled successfully."