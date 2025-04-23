#!/bin/bash

set -e

# Determine script directory dynamically to ensure everything runs in ./scripts/api/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Help function
show_help() {
    echo "Usage: $0 [--execution=process|container|service]"
    echo
    echo "Description:"
    echo "  This script start the miner's components"
    echo
    echo "Options:"
    echo "  --execution   Specify the execution method (default: service)"
    echo "  --recreate    True if you want to recreate the container when starting it, false otherwise."
    echo "  --help        Show this help message"
    exit 0
}

OPTIONS="e:rh"
LONGOPTIONS="execution:recreate,help"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

EXECUTION=service
RECREATE=false

# Parse arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        -e |--execution)
            EXECUTION="$2"
            shift 2
        ;;
        -r|--recreate)
            RECREATE=true
            shift
        ;;
        -h | --help)
            show_help
            exit 0
        ;;
        *)
            echo "Unrecognized option '$1'"
            exit 1
        ;;
    esac
done

# Build the command and arguments
CMD="./neuron/scripts/neuron_start.sh --execution $EXECUTION"
if [[ "$RECREATE" == "true" || "$RECREATE" == "True" ]]; then
    CMD+=" --recreate"
fi

# Setup the auto upgrade as container
eval "$CMD"