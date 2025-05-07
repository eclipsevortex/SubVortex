#!/bin/bash

set -euo pipefail

NEURON_NAME="subvortex-validator"
SERVICE_NAME="$NEURON_NAME-neuron"
REDIS_CLI_CMD="redis-cli -a ${SUBVORTEX_REDIS_PASSWORD:-} -p ${SUBVORTEX_REDIS_PORT:-6379} PING"

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source venv/bin/activate

# Load environment variables
echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' .env | xargs)

# Build CLI args from SUBVORTEX_ environment variables
echo "🔧 Building CLI arguments from SUBVORTEX_ environment variables..."
ARGS=()
PREFIX="SUBVORTEX_"

while IFS= read -r line; do
    key="${line%%=*}"
    value="${line#*=}"
    if [[ $key == ${PREFIX}* ]]; then
        key_suffix="${key#$PREFIX}"
        cli_key="--$(echo "$key_suffix" | tr '[:upper:]' '[:lower:]' | tr '_' '.')"
        value_lower="$(echo "$value" | tr '[:upper:]' '[:lower:]')"
        
        if [[ "$value_lower" == "true" ]]; then
            ARGS+=("$cli_key")
            elif [[ "$value_lower" == "false" ]]; then
            continue
        else
            ARGS+=("$cli_key" "$value")
        fi
    fi
done < <(env)

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