#!/bin/bash

set -euo pipefail

NEURON_NAME="subvortex-miner"
SERVICE_NAME="$NEURON_NAME-neuron"

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

source ../../scripts/utils.sh

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source venv/bin/activate

# Load environment variables
echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' .env | xargs)

# Build CLI args from SUBVORTEX_ environment variables
eval "ARGS=( $(convert_env_var_to_args) )"

# Start or reload PM2 process
echo "🔍 Checking PM2 process: $SERVICE_NAME..."
if pm2 describe "$SERVICE_NAME" >/dev/null 2>&1; then
    if [[ ${#ARGS[@]} -eq 0 ]]; then
        echo "🔁 No additional CLI args, reloading service normally..."
        pm2 reload "$SERVICE_NAME" --update-env
    else
        echo "🔁 Restarting $SERVICE_NAME with updated CLI args: ${ARGS[*]}"
        pm2 restart "$SERVICE_NAME" --update-env -- "${ARGS[@]}"
    fi
else
    echo "🚀 No existing process found — starting $SERVICE_NAME via PM2..."
    pm2 start src/main.py \
    --name "$SERVICE_NAME" \
    --interpreter "venv/bin/python3" -- \
    "${ARGS[@]}"
fi


# ✅ Final check — Is Redis responding?
echo "✅ $SERVICE_NAME is running via PM2 and is online."
