#!/bin/bash

# This script setup and run a local subtensor
# TODO: check the valud for each argument is an expected one

show_help() {
cat << EOF
Usage: ${0##*/} [-e ARG] [-n ARG] [-h] -- Install and run redis

    -e | --exec ARG      type of execution of the redis instance (process or docker), default docker
    -n | --network ARG   network to run the local subtensor on (e.g localnet, testnet and mainnet), default mainnet
    -h | --help          display the help
EOF
}

OPTIONS="e:n:h"
LONGOPTIONS="exec:,network:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

EXEC_TYPE='docker'
NETWORK='mainnet'

while [ "$#" -gt 0 ]; do
    case "$1" in
        -e | --exec)
            EXEC_TYPE="$2"
            shift 2
        ;;
        -n | --network)
            NETWORK="$2"
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

# Get the base path
current_dir=$(pwd)
relative_dir="SubVortex/scripts/subtensor"
if [[ $current_dir != *"SubVortex"* ]]; then
    BASE="${current_dir%/}/${relative_dir%/}"
else
    BASE="${current_dir%/}/${relative_dir#*/}"
fi

# Setup subtensor
OPTIONS=$([[ "$EXEC_TYPE" == "process" ]] && echo "-n $NETWORK" || echo "")
$BASE/$EXEC_TYPE/subtensor_"$EXEC_TYPE"_setup.sh $OPTIONS

# Start subtensor
$BASE/$EXEC_TYPE/subtensor_"$EXEC_TYPE"_start.sh -n $NETWORK -p