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

# Start or reload PM2
if pm2 list | grep -q "$SERVICE_NAME"; then
  echo "🔁 Reloading $SERVICE_NAME"
  pm2 reload "$SERVICE_NAME" --update-env
else
  echo "🚀 Starting $SERVICE_NAME"
  pm2 start "$DEPLOY_LINK/subvortex/validator/neuron/src/main.py" \
    --name "$SERVICE_NAME" \
    --interpreter python3 -- \
    "${ARGS[@]}"
fi

echo "✅ $SERVICE_NAME is running"
