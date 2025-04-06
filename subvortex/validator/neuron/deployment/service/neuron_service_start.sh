#!/bin/bash

set -e

SERVICE_NAME="subvortex-validator"

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

# Build CLI args from SUBVORTEX_ environment variables
ARGS=()
PREFIX="SUBVORTEX_"

while IFS='=' read -r key value; do
  if [[ $key == ${PREFIX}* ]]; then
    key_suffix="${key#$PREFIX}"
    cli_key="--$(echo "$key_suffix" | tr '[:upper:]' '[:lower:]' | tr '_' '.')"
    if [[ "$(echo "$value" | tr '[:upper:]' '[:lower:]')" == "true" ]]; then
      ARGS+=("$cli_key")
    else
      ARGS+=("$cli_key" "$value")
    fi
  fi
done < <(env)

# Build the full ExecStart line
PYTHON_EXEC="/root/subvortex/subvortex/validator/neuron/venv/bin/python3"
MODULE="subvortex.validator.neuron.src.main"
FULL_EXEC_START="$PYTHON_EXEC -m $MODULE ${ARGS[*]}"

# Path setup
SERVICE_NAME="subvortex-validator"
TEMPLATE_PATH="./deployment/templates/${SERVICE_NAME}.service"
TEMP_TEMPLATE="/tmp/${SERVICE_NAME}.service.template"

# Replace ExecStart in template before envsubst
sed "s|^ExecStart=.*|ExecStart=$FULL_EXEC_START|" "$TEMPLATE_PATH" > "$TEMP_TEMPLATE"

# Use envsubst to inject any other environment vars
envsubst < "$TEMP_TEMPLATE" | tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null

# Prepare the log
sudo mkdir -p /var/log/$SERVICE_NAME
sudo chown root:root /var/log/$SERVICE_NAME

# Reload and (re)start the service
systemctl daemon-reexec
systemctl daemon-reload

if systemctl is-active --quiet $SERVICE_NAME; then
  systemctl restart $SERVICE_NAME
else
  systemctl start $SERVICE_NAME
fi

echo "✅ Validator started successfully"
