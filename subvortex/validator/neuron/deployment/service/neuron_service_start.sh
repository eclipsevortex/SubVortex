#!/bin/bash

set -euo pipefail

NEURON_NAME="subvortex-validator"
SERVICE_NAME="$NEURON_NAME-neuron"

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

source ../../../scripts/utils/utils.sh

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
envsubst < "$TEMP_TEMPLATE" | sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null

# Prepare log folder
echo "📁 Preparing log directory for $NEURON_NAME..."
sudo mkdir -p /var/log/$NEURON_NAME
sudo chown root:root /var/log/$NEURON_NAME

# Reload systemd
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

# Start or restart the service
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "🔁 $SERVICE_NAME is already running — restarting..."
    sudo systemctl restart "$SERVICE_NAME"
else
    echo "🚀 Starting $SERVICE_NAME for the first time..."
    sudo systemctl start "$SERVICE_NAME"
fi

# Final status check
echo "✅ Validator Neuron started successfully."