#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-validator-metagraph
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

echo "🚀 Starting $SERVICE_NAME..."

# Fallback to script location if PROJECT_WORKING_DIR is not set
if [[ -z "$PROJECT_WORKING_DIR" ]]; then
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_WORKING_DIR="$(realpath "$SCRIPT_PATH/../../../../../")"
  echo "📁 PROJECT_WORKING_DIR not set — using fallback: $PROJECT_WORKING_DIR"
else
  echo "📁 Using PROJECT_WORKING_DIR from environment: $PROJECT_WORKING_DIR"
fi

PROJECT_EXECUTION_DIR="${SUBVORTEX_EXECUTION_DIR:-$PROJECT_WORKING_DIR}"
SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/validator/metagraph"

echo "🔍 Checking $SERVICE_NAME..."
if pm2 describe "$SERVICE_NAME" >/dev/null 2>&1; then
    CURRENT_CWD=$(pm2 info "$SERVICE_NAME" | grep -E 'exec cwd' | sed -E 's/.*exec cwd\s+│\s+([^ ]+)\s+.*/\1/')
    if [[ "$CURRENT_CWD" != "$SERVICE_WORKING_DIR" ]]; then
        echo "⚠️  CWD mismatch for $SERVICE_NAME (current: $CURRENT_CWD, expected: $SERVICE_WORKING_DIR)"
        echo "💥 Deleting $SERVICE_NAME to recreate with updated CWD..."
        pm2 delete "$SERVICE_NAME"
    fi
fi

# Set the venv dir
VENV_DIR="$SERVICE_WORKING_DIR/venv"

echo "🐍 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' $SERVICE_WORKING_DIR/.env | xargs)

# Start or reload process
echo "🔍 Checking $SERVICE_NAME..."
if pm2 describe "$SERVICE_NAME" >/dev/null 2>&1; then
    if pm2 status "$SERVICE_NAME" | grep -q "online"; then
        echo "🔁 $SERVICE_NAME is already running — reloading..."
        pm2 reload "$SERVICE_NAME" --update-env
    else
        echo "♻️ $SERVICE_NAME exists but not running — restarting..."
        pm2 restart "$SERVICE_NAME" --update-env
    fi
else
    echo "🚀 No existing process found — starting $SERVICE_NAME via PM2..."
    pm2 start "$SERVICE_WORKING_DIR/src/main.py" \
    --name "$SERVICE_NAME" \
    --cwd "$SERVICE_WORKING_DIR" \
    --interpreter "$VENV_DIR/bin/python3"
fi


echo "✅ $SERVICE_NAME started successfully."