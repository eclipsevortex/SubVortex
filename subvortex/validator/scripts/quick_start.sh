#!/bin/bash

set -euo pipefail

SERVICE_NAME=
PROJECT_WORKING_DIR="${SUBVORTEX_WORKING_DIR:-}"

# Fallback to script location if PROJECT_WORKING_DIR is not set
if [[ -z "$PROJECT_WORKING_DIR" ]]; then
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_WORKING_DIR="$(realpath "$SCRIPT_PATH/../../../")"
  echo "📁 PROJECT_WORKING_DIR not set — using fallback: $PROJECT_WORKING_DIR"
else
  echo "📁 Using PROJECT_WORKING_DIR from environment: $PROJECT_WORKING_DIR"
fi

PROJECT_EXECUTION_DIR="${SUBVORTEX_EXECUTION_DIR:-$PROJECT_WORKING_DIR}"
NEURON_WORKING_DIR="$PROJECT_WORKING_DIR/subvortex/validator"

# Load some utils
source "$NEURON_WORKING_DIR/../scripts/utils.sh"

# Help function
show_help() {
    echo "Usage: $0 [--execution=process|container|service]"
    echo
    echo "Description:"
    echo "  This script start the validator's components"
    echo
    echo "Options:"
    echo "  --execution   Specify the execution method (default: service)"
    echo "  --help        Show this help message"
    exit 0
}

OPTIONS="e:h"
LONGOPTIONS="execution:,help:"

EXECUTION=service

# Parse arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        -e |--execution)
            EXECUTION="$2"
            shift 2
        ;;
        -h | --help)
            show_help
            exit 0
        ;;
        --)
            shift
            break
        ;;
        *)
            echo "Unrecognized option '$1'"
            exit 1
        ;;
    esac
done

# Check maandatory args
check_required_args EXECUTION

echo "🔧 Running setup for validator components..."
"$NEURON_WORKING_DIR/redis/scripts/redis_setup.sh" --execution $EXECUTION
"$NEURON_WORKING_DIR/metagraph/scripts/metagraph_setup.sh" --execution $EXECUTION
"$NEURON_WORKING_DIR/neuron/scripts/neuron_setup.sh" --execution $EXECUTION

echo "🚀 Starting validator components..."
"$NEURON_WORKING_DIR/redis/scripts/redis_start.sh" --execution $EXECUTION
"$NEURON_WORKING_DIR/metagraph/scripts/metagraph_start.sh" --execution $EXECUTION
"$NEURON_WORKING_DIR/neuron/scripts/neuron_start.sh" --execution $EXECUTION
