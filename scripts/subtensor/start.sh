#!/bin/bash

NETWORK=${1:-"localnet"}
EXEC_TYPE=${2:-binary}
ROOT=${3:-$HOME}

# Go the subtensor repository
cd $ROOT/subtensor

echo "Starting subtensor on $NETWORK..."

run_local_subtensor() {
    # Create the start script
    echo "FEATURES='pow-faucet runtime-benchmarks' bash scripts/localnet.sh" >> setup_and_run.sh
    chmod +x setup_and_run.sh

    # Start the local subtensor
    pm2 start setup_and_run.sh --name subtensor

    echo "Subtensor on network localnet is up"
}

run_remote_subtensor() {
    # Compiling
    cargo build --release --features pow-faucet --features runtime-benchmarks --locked

    # Run 
    ./scripts/run/subtensor.sh -e $EXEC_TYPE --network $NETWORK --node-type lite

    echo "Subtensor on network $NETWORK is up"
}

if [[ $NETWORK == "localnet" ]]; then
    run_local_subtensor
fi

if [[ $NETWORK == "testnet" ]] || [[ $NETWORK == "mainnet" ]]; then
    run_remote_subtensor
fi

# Go the root
cd $ROOT