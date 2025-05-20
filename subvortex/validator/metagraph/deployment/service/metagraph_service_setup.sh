#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-validator-metagraph
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

if [[ "$EUID" -ne 0 ]]; then
  echo "🛑 Must be run as root. Re-running with sudo..."
  exec sudo "$0" "$@"
fi

echo "🔧 Starting $SERVICE_NAME setup..."

# Fallback to script location if PROJECT_WORKING_DIR is not set
if [[ -z "$PROJECT_WORKING_DIR" ]]; then
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_WORKING_DIR="$(realpath "$SCRIPT_PATH/../../../../../")"
  echo "📁 PROJECT_WORKING_DIR not set — using fallback: $PROJECT_WORKING_DIR"
else
  echo "📁 Using PROJECT_WORKING_DIR from environment: $PROJECT_WORKING_DIR"
fi

SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/validator/metagraph"
SERVICE_TEMPLATE="$SERVICE_WORKING_DIR/deployment/templates/$SERVICE_NAME.service"
SERVICE_LOG_DIR="/var/log/subvortex-validator"
TEMP_SERVICE_FILE="/tmp/$SERVICE_NAME.service"

# --- Load environment variables from .env file ---
ENV_FILE="$SERVICE_WORKING_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
  echo "🌱 Loading environment variables from $ENV_FILE"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
else
  echo "⚠️ No .env file found at $ENV_FILE"
fi

# --- Python project setup ---
VENV_DIR="$SERVICE_WORKING_DIR/venv"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "🐍 Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

echo "🐍 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "📦 Installing Python dependencies..."
pip install -r "$SERVICE_WORKING_DIR/requirements.txt"

echo "📚 Installing Python project in editable mode..."
pip install -e "$PROJECT_WORKING_DIR"

echo "🧘 Deactivating virtual environment..."
deactivate


echo "📁 Preparing log directory..."
mkdir -p "$SERVICE_LOG_DIR"
chown root:root "$SERVICE_LOG_DIR"

# --- Create log files and adjust permissions ---
LOG_PREFIX="$SERVICE_LOG_DIR/subvortex-validator-metagraph"
echo "🔒 Adjusting permissions for logs with prefix: $LOG_PREFIX"

# Ensure the log directory exists
mkdir -p "$(dirname "$LOG_PREFIX")"

# Create the log files if they don't exist
touch "${LOG_PREFIX}.log" "${LOG_PREFIX}-error.log"

# Set correct ownership
chown root:root "${LOG_PREFIX}.log" "${LOG_PREFIX}-error.log"

echo "📝 Preparing systemd service file from template..."
sed "s|<WORKING_DIR>|$PROJECT_WORKING_DIR|g" "$SERVICE_TEMPLATE" > "$TEMP_SERVICE_FILE"

echo "📝 Installing systemd service file to $SERVICE_FILE..."
mv "$TEMP_SERVICE_FILE" "$SERVICE_FILE"

chmod 644 "$SERVICE_FILE"

echo "🔄 Reloading systemd and completing setup..."
systemctl daemon-reexec
systemctl daemon-reload

echo "✅ $SERVICE_NAME installed successfully."