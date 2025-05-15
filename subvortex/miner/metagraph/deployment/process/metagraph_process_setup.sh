#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-metagraph
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

SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/miner/metagraph"

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