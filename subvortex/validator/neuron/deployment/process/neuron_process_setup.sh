#!/bin/bash

set -euo pipefail

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

echo "📦 Starting Validator Neuron setup..."

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
if [[ -f "requirements.txt" ]]; then
    echo "📚 Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found. Skipping dependency installation."
fi

# Install SubVortex in Editable Mode
echo "📚 Installing SubVortex package in editable mode..."
pip install -e ../../../

# Deactivate virtual environment
echo "🛑 Deactivating virtual environment..."
deactivate

echo "✅ Validator Neuron setup completed successfully."
