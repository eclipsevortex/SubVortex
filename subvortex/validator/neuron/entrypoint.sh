#!/bin/bash -eu

# Set EXTRA ARGS
EXTRA_ARGS=()

if [[ "$SUBVORTEX_DRY_RUN" == "True" ]]; then
  EXTRA_ARGS+=("--dry_run")
fi

if [ $# -eq 0 ]; then
    python src/main.py \
    --netuid "${SUBVORTEX_NETUID}" \
    "${EXTRA_ARGS[@]}"
else
    exec "$@"
fi