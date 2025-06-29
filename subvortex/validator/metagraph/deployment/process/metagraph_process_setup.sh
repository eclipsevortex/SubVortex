#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-validator-metagraph
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

echo "🔧 Starting $SERVICE_NAME setup..."

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
# Set the venv dir
VENV_DIR="$SERVICE_WORKING_DIR/venv"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "🐍 Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

echo "🐍 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "📦 Installing Python dependencies..."
pip install -r $SERVICE_WORKING_DIR/requirements.txt

echo "📚 Installing Python project in editable mode..."
pip install -e "$PROJECT_WORKING_DIR"

echo "🧘 Deactivating virtual environment..."
deactivate



echo "✅ $SERVICE_NAME installed successfully."