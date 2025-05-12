#!/bin/bash

set -euo pipefail

# Ensure script run as root
if [[ "$EUID" -ne 0 ]]; then
    echo "🛑 This script must be run as root. Re-running with sudo..."
    exec sudo "$0" "$@"
fi

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

source ../../scripts/utils.sh

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source venv/bin/activate

# Load environment variables
echo "🔍 Loading environment variables from .env..."
export $(grep -v '^#' .env | xargs)

# Build CLI args from SUBVORTEX_ environment variables
eval "ARGS=( $(convert_env_var_to_args) )"

# Build the full ExecStart command
PYTHON_EXEC="venv/bin/python3"
MODULE="subvortex.validator.neuron.src.main"
FULL_EXEC_START="$PYTHON_EXEC -m $MODULE ${ARGS[*]}"
USE_LOCAL_WORKDIR="${SUBVORTEX_USE_LOCAL_WORKDIR:-}"

# Determine WorkingDirectory based on --local
WORKING_DIR="/root/subvortex/subvortex/validator/neuron"
if [[ "${USE_LOCAL_WORKDIR,,}" == "true" ]]; then
    WORKING_DIR="$(pwd)"
fi

echo "📝 Building systemd service file..."

TEMPLATE_PATH="./deployment/templates/${SERVICE_NAME}.service"
TEMP_TEMPLATE="/tmp/${SERVICE_NAME}.service.template"

# Replace ExecStart in template before envsubst
sed -e "s|^ExecStart=.*|ExecStart=$WORKING_DIR/$FULL_EXEC_START|" \
-e "s|^EnvironmentFile=.*|EnvironmentFile=$WORKING_DIR/.env|" \
-e "s|^WorkingDirectory=.*|WorkingDirectory=$WORKING_DIR|" \
"$TEMPLATE_PATH" > "$TEMP_TEMPLATE"

# Inject any remaining env vars
envsubst < "$TEMP_TEMPLATE" | tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null

# Prepare log folder
echo "📁 Preparing log directory for $NEURON_NAME..."
mkdir -p /var/log/$NEURON_NAME
chown root:root /var/log/$NEURON_NAME

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reexec
systemctl daemon-reload

# Start or restart the service
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "🔁 $SERVICE_NAME is already running — restarting..."
    systemctl restart "$SERVICE_NAME"
else
    echo "🚀 Starting $SERVICE_NAME for the first time..."
    systemctl start "$SERVICE_NAME"
fi

# Final status check
echo "✅ Validator Neuron started successfully."