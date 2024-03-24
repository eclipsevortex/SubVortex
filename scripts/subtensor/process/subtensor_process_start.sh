#!/bin/bash

source ${BASH_SOURCE%/*}/../../utils/machine.sh

show_help() {
cat << EOF
Usage: ${0##*/} [-n ARG] [-h] -- Start the local subtensor

    -n | --network ARG      network to run the local subtensor on (e.g localnet, testnet and mainnet), default mainnet
    -h | --help             display the help
EOF
}

OPTIONS="n:h"
LONGOPTIONS="network:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

NETWORK="mainnet"

while [ "$#" -gt 0 ]; do
    case "$1" in
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

run_local_subtensor() {
    # Create the start script
    echo "FEATURES='pow-faucet runtime-benchmarks' bash scripts/localnet.sh" >> setup_and_run.sh
    chmod +x setup_and_run.sh
    
    # Start the local subtensor
    pm2 start setup_and_run.sh --name subtensor
    echo -e "\e[32mSubtensor on network $NETWORK is up\e[0m"
}

run_remote_subtensor() {
    $BASE/scripts/subtensor_start.sh -e binary --network $NETWORK --node-type lite
    echo -e "\e[32mSubtensor on network $NETWORK is up\e[0m"
}

# Go to the subtensor directory
cd subtensor

if [[ $NETWORK == "localnet" ]]; then
    run_local_subtensor
fi

if [[ $NETWORK == "testnet" ]] || [[ $NETWORK == "mainnet" ]]; then
    run_remote_subtensor
fi