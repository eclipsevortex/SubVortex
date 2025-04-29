#!/bin/bash

set -e

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found. Skipping dependency installation."
fi

# Install SubVortex in Editable Mode
pip install -e ../../../

# Deactivate virtual environment
deactivate

echo "✅ Miner Neuron setup successfully"
