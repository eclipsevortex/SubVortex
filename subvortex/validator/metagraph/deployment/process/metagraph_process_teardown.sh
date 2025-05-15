#!/bin/bash
w
set -euo pipefail

SERVICE_NAME=subvortex-validator-metagraph
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

SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/validator/metagraph"

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

# --- Python virtualenv cleanup ---
# Set the venv dir
VENV_DIR="$SERVICE_WORKING_DIR/venv"

echo "🔍 Checking for virtual environment..."
if [[ -d "$VENV_DIR" ]]; then
    echo "🧹 Removing virtual environment..."
    rm -rf "$VENV_DIR"
else
    echo "ℹ️ Virtual environment not found. Skipping removal."
fi


echo "✅ $SERVICE_NAME uninstalled successfully."