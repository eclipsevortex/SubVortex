#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-neuron
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

SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/miner/neuron"

# Set the venv dir
VENV_DIR="$SERVICE_WORKING_DIR/venv"

echo "🐍 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' $SERVICE_WORKING_DIR/.env | xargs)

# Start or reload process
echo "🔍 Checking $SERVICE_NAME..."
if pm2 describe "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "🔁 Restarting $SERVICE_NAME with updated CLI args: ${ARGS[*]}"
    pm2 restart "$SERVICE_NAME" --update-env
else
    echo "🚀 No existing process found — starting $SERVICE_NAME via PM2..."
    pm2 start "$SERVICE_WORKING_DIR/src/main.py" \
    --name "$SERVICE_NAME" \
    --cwd "$SERVICE_WORKING_DIR" \
    --interpreter "$VENV_DIR/bin/python3"
fi


echo "✅ $SERVICE_NAME started successfully."