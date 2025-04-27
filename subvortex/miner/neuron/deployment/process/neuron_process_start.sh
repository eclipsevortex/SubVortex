#!/bin/bash

set -e

SERVICE_NAME="subvortex-miner"

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

resolve_path() {
    local path="$1"
    
    if command -v realpath >/dev/null 2>&1; then
        realpath "$path"
    else
        # Fallback for macOS (readlink -f may not exist)
        # Uses Python to resolve real path
        python3 -c "import os; print(os.path.realpath('$path'))"
    fi
}

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Define deployment paths
DEPLOY_SOURCE="$SCRIPT_DIR/../../../../../"
DEPLOY_SOURCE=$(resolve_path "$DEPLOY_SOURCE")
DEPLOY_LINK="$HOME/subvortex"

# Create parent directory if needed
mkdir -p "$(dirname "$DEPLOY_LINK")"

# Atomically update symlink
TEMP_LINK="${DEPLOY_LINK}.tmp"

# Create/update the temp symlink
ln -sfn "$DEPLOY_SOURCE" "$TEMP_LINK"

# On macOS and Linux: remove old symlink and rename temp
if [ -L "$DEPLOY_LINK" ] || [ -e "$DEPLOY_LINK" ]; then
    rm -rf "$DEPLOY_LINK"
fi
mv "$TEMP_LINK" "$DEPLOY_LINK"

echo "🔗 Symlink set: $DEPLOY_LINK → $DEPLOY_SOURCE"

# Build CLI args from SUBVORTEX_ environment variables
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
            elif [[ $value_lower == "false" ]]; then
            continue
        else
            ARGS+=("$cli_key" "$value")
        fi
    fi
done < <(env)

# Start or reload PM2
if pm2 list | grep -q "$SERVICE_NAME"; then
    if [[ ${#ARGS[@]} -eq 0 ]]; then
        echo "🔁  No additional CLI args, reloading service normally..."
        pm2 reload "$SERVICE_NAME" --update-env
    else
        echo "🔁  Restarting $SERVICE_NAME with updated CLI args: ${ARGS[*]}"
        pm2 restart "$SERVICE_NAME" --update-env -- "${ARGS[@]}"
    fi
else
    echo "🚀 Starting $SERVICE_NAME"
    pm2 start "$DEPLOY_LINK/subvortex/miner/neuron/src/main.py" \
    --name "$SERVICE_NAME" \
    --interpreter python3 -- \
    "${ARGS[@]}"
fi

echo "✅ $SERVICE_NAME is running"
