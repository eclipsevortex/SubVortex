#!/bin/bash

set -e

# Help function
show_help() {
    echo "Usage: $0 [--execution=process|container|service]"
    echo
    echo "Options:"
    echo "  --execution   Specify the execution method (default: service)"
    echo "  --help        Show this help message"
    exit 0
}

OPTIONS="e:h"
LONGOPTIONS="execution:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

METHOD=service

# Parse arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        -e |--execution)
            METHOD="$2"
            shift 2
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

# Stop and teardown redis 
./subvortex/validator/redis/scripts/redis_stop.sh --execution $METHOD
./subvortex/validator/redis/scripts/redis_teardown.sh --execution $METHOD

# Stop and teardown neuron
./subvortex/validator/neuron/scripts/neuron_stop.sh --execution $METHOD
./subvortex/validator/neuron/scripts/neuron_teardown.sh --execution $METHOD