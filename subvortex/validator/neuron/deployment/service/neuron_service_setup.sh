#!/bin/bash

set -euo pipefail

# Ensure script run as root
if [[ "$EUID" -ne 0 ]]; then
    echo "🛑 This script must be run as root. Re-running with sudo..."
    exec sudo "$0" "$@"
fi

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

echo "🐍 Setting up Python virtual environment..."

# Create virtual environment
echo "🔧 Creating venv..."
python3 -m venv venv

# Activate virtual environment
echo "🚀 Activating venv..."
source venv/bin/activate

# Install dependencies
if [[ -f "requirements.txt" ]]; then
    echo "📦 Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found — skipping dependency installation."
fi

# Ensure pyproject.toml is present (local execution only)
if [[ ! -f "../../../pyproject.toml" ]]; then
    if [[ -f "../../../pyproject-miner.toml" ]]; then
        echo "📄 pyproject.toml not found, copying pyproject-validator.toml..."
        cp ../../../pyproject-validator.toml ../../../pyproject.toml
    else
        echo "❌ pyproject.toml and pyproject-validator.toml both not found. Cannot proceed."
        exit 1
    fi
fi

# Install SubVortex project in editable mode
echo "📚 Installing SubVortex project in editable mode..."
pip install -e ../../../

# Deactivate virtual environment
echo "🛑 Deactivating venv..."
deactivate

echo "✅ Validator Neuron setup completed successfully."
