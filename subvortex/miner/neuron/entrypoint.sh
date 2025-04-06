#!/bin/bash -eu

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Build CLI args from SUBVORTEX_ environment variables
ARGS=()
PREFIX="SUBVORTEX_"

while IFS= read -r line; do
  key="${line%%=*}"
  value="${line#*=}"
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

if [ $# -eq 0 ]; then
    python ./subvortex/miner/neuron/src/main.py \
    "${ARGS[@]}"
else
    exec "$@"
fi