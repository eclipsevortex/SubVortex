#!/bin/bash

set -euo pipefail

# Determine working directory: prefer SUBVORTEX_WORKING_DIR, fallback to script location
SCRIPT_DIR="$(cd "$(dirname "$(python3 -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$0")")" && pwd)"

# Find project root by walking up until LICENSE is found
find_project_root() {
    local dir="$1"
    while [[ "$dir" != "/" ]]; do
        [[ -f "$dir/LICENSE" ]] && { echo "$dir"; return; }
        dir="$(dirname "$dir")"
    done
    return 1
}

PROJECT_ROOT="$(find_project_root "$SCRIPT_DIR")" || {
    echo "❌ Could not detect project root (LICENSE not found)"
    exit 1
}

# Resolve final working directory
if [[ -n "${SUBVORTEX_WORKING_DIR:-}" ]]; then
    REL_PATH="${SCRIPT_DIR#$PROJECT_ROOT/}"
    TARGET_DIR="$SUBVORTEX_WORKING_DIR/$REL_PATH"
    [[ -d "$TARGET_DIR" ]] || { echo "❌ Target directory does not exist: $TARGET_DIR"; exit 1; }
    echo "📁 Using SUBVORTEX_WORKING_DIR: $TARGET_DIR"
    cd "$TARGET_DIR/../.."
else
    echo "📁 Using fallback PROJECT_ROOT: $SCRIPT_DIR"
    cd "$SCRIPT_DIR/../.."
fi

echo "📍 Working directory: $(pwd)"

NEURON_NAME="subvortex-validator"
SERVICE_NAME="$NEURON_NAME-neuron"
REDIS_CLI_CMD="redis-cli -a ${SUBVORTEX_REDIS_PASSWORD:-} -p ${SUBVORTEX_REDIS_PORT:-6379} PING"

source ../../scripts/utils.sh

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source venv/bin/activate

# Load environment variables
echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' .env | xargs)

# Build CLI args from SUBVORTEX_ environment variables
eval "ARGS=( $(convert_env_var_to_args) )"

# Check for existing PM2 process and remove if config differs
if pm2 jlist | jq -e ".[] | select(.name==\"$SERVICE_NAME\")" > /dev/null; then
    EXISTING_CWD="$(pm2 jlist | jq -r ".[] | select(.name==\"$SERVICE_NAME\") | .pm2_env.pm_cwd")"
    CURRENT_CWD="$(pwd)"

    if [[ "$EXISTING_CWD" != "$CURRENT_CWD" ]]; then
        pm2 delete "$SERVICE_NAME"
    fi
fi

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
    pm2 start "$(pwd)/src/main.py" \
    --name "$SERVICE_NAME" \
    --cwd "$(pwd)" \
    --interpreter "$(pwd)/venv/bin/python3" -- \
    "${ARGS[@]}"
fi

# ✅ Final check — Is Redis responding?
echo "✅ $SERVICE_NAME is running via PM2 and is online."