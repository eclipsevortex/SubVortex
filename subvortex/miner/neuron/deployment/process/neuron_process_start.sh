#!/bin/bash

set -euo pipefail

NEURON_NAME="subvortex-miner"
SERVICE_NAME="$NEURON_NAME-neuron"

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# echo "🔍 Resolving deployment paths..."

# resolve_path() {
#     local path="$1"
    
#     if command -v realpath >/dev/null 2>&1; then
#         realpath "$path"
#     else
#         # Fallback if realpath is not available
#         python3 -c "import os; print(os.path.realpath('$path'))"
#     fi
# }

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source venv/bin/activate

# Load environment variables
echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' .env | xargs)

# # Define deployment paths
# DEPLOY_SOURCE="$SCRIPT_DIR/../../../../../"
# DEPLOY_SOURCE=$(resolve_path "$DEPLOY_SOURCE")
# DEPLOY_LINK="$HOME/subvortex"

# echo "📁 Ensuring parent directory for symlink exists..."
# mkdir -p "$(dirname "$DEPLOY_LINK")"

# # Create/update symlink atomically
# TEMP_LINK="${DEPLOY_LINK}.tmp"

# echo "🔗 Creating temporary symlink..."
# ln -sfn "$DEPLOY_SOURCE" "$TEMP_LINK"

# echo "🧹 Removing old symlink if necessary..."
# if [ -L "$DEPLOY_LINK" ] || [ -e "$DEPLOY_LINK" ]; then
#     rm -rf "$DEPLOY_LINK"
# fi

# echo "🔀 Moving temporary symlink to final location..."
# mv "$TEMP_LINK" "$DEPLOY_LINK"

# echo "✅ Symlink set: $DEPLOY_LINK → $DEPLOY_SOURCE"

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
    pm2 start "$HOME/subvortex/subvortex/miner/neuron/src/main.py" \
        --name "$SERVICE_NAME" \
        --interpreter python3 -- \
        "${ARGS[@]}"
fi

# Save PM2 state
echo "💾 Saving PM2 process list for startup persistence..."
pm2 save

echo "✅ Miner Neuron started successfully."
