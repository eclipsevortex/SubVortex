#!/bin/bash

set -e

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Start building the argument list
ARGS=()

# Prefix to look for
PREFIX="SUBVORTEX_"

# Loop through all environment variables starting with SUBVORTEX_
while IFS='=' read -r key value; do
  if [[ $key == ${PREFIX}* ]]; then
    # Remove prefix and convert to CLI format: UPPER_SNAKE → --lower.dotted
    key_suffix="${key#$PREFIX}"                      # Strip prefix
    cli_key="--$(echo "$key_suffix" | tr '[:upper:]' '[:lower:]' | tr '_' '.')"

    # Check if value is boolean true
    if [[ "$(echo "$value" | tr '[:upper:]' '[:lower:]')" == "true" ]]; then
      ARGS+=("$cli_key")
    else
      ARGS+=("$cli_key" "$value")
    fi
  fi
done < <(env)

# Start with PM2
pm2 start src/main.py \
  --name subvortex-validator \
  --interpreter python3 -- \
  "${ARGS[@]}"

echo "✅ Validator started successfully"
