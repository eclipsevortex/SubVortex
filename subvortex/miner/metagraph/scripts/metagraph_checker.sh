#!/bin/bash

set -euo pipefail

SERVICE_NAME=subvortex-miner-metagraph
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

# Fallback to script location if PROJECT_WORKING_DIR is not set
if [[ -z "$PROJECT_WORKING_DIR" ]]; then
    SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_WORKING_DIR="$(realpath "$SCRIPT_PATH/../../../../")"
    echo "📁 PROJECT_WORKING_DIR not set — using fallback: $PROJECT_WORKING_DIR"
else
    echo "📁 Using PROJECT_WORKING_DIR from environment: $PROJECT_WORKING_DIR"
fi

PROJECT_EXECUTION_DIR="${SUBVORTEX_EXECUTION_DIR:-$PROJECT_WORKING_DIR}"
SERVICE_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/miner/metagraph"

# Activate the virtual environment
source $SERVICE_WORKING_DIR/venv/bin/activate

# Execute the querier
python3 $SERVICE_WORKING_DIR/src/checker.py "$@"
