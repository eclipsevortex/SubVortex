#!/bin/bash

source ${BASH_SOURCE%/*}/../../utils/machine.sh

show_help() {
cat << EOF
Usage: ${0##*/} [-n ARG] [-h] -- Start the local subtensor

    -n | --network ARG      network to run the local subtensor on (e.g localnet, testnet and mainnet), default mainnet
    -p | --pm2              if provided, run the local subtensor with pm2, false otherwise
    -h | --help             display the help
EOF
}

OPTIONS="n:ph"
LONGOPTIONS="network:,pm2:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

NETWORK="mainnet"
WITH_PM2=false

while [ "$#" -gt 0 ]; do
    case "$1" in
        -n | --network)
            NETWORK="$2"
            shift 2
        ;;
        -p | --pm2)
            WITH_PM2=true
            shift 1
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
    if [[ $WITH_PM2 == true ]]; then
        pm2 start $BASE/scripts/subtensor_start.sh -f \
            --name subtensor -- \
            -e binary \
            --network $NETWORK \
            --node-type lite
    else
        $BASE/scripts/subtensor_start.sh -e binary --network $NETWORK --node-type lite
    fi
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