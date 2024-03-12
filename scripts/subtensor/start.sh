#!/bin/bash

NETWORK=${1:-"mainnet"}
EXEC_TYPE=${2:-binary}
ROOT=${3:-$HOME}

# Go the subtensor repository
cd $ROOT/subtensor

echo "Starting subtensor on network $NETWORK..."

run_local_subtensor() {
    # Create the start script
    echo "FEATURES='pow-faucet runtime-benchmarks' bash scripts/localnet.sh" >> setup_and_run.sh
    chmod +x setup_and_run.sh
    
    # Start the local subtensor
    pm2 start setup_and_run.sh --name subtensor
    
    echo -e "\e[32mSubtensor on network $NETWORK is up\e[0m"
}

run_remote_subtensor() {
    # Override run script
    # Bootnodes is wrong for testnet
    cp $HOME/SubVortex/scripts/subtensor/run.sh $HOME/subtensor/scripts/run/subtensor.sh

    # Run
    ./scripts/run/subtensor.sh -e $EXEC_TYPE --network $NETWORK --node-type lite
    echo -e "\e[32mSubtensor on network $NETWORK is up\e[0m"
}

if [[ $NETWORK == "localnet" ]]; then
    run_local_subtensor
fi

if [[ $NETWORK == "testnet" ]] || [[ $NETWORK == "mainnet" ]]; then
    run_remote_subtensor
fi

# Go the root
cd $ROOT