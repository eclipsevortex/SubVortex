#!/bin/bash

ROOT=${1:-$HOME}

# Create a coldkey for the owner role
wallet=${1:-owner}

# Go the subtensor repository
cd $ROOT/subtensor

# Create the start script
echo "FEATURES='pow-faucet runtime-benchmarks' BT_DEFAULT_TOKEN_WALLET=$(cat ~/.bittensor/wallets/$wallet/coldkeypub.txt | grep -oP '"ss58Address": "\K[^"]+') bash scripts/localnet.sh" >> setup_and_run.sh
chmod +x setup_and_run.sh

# Start the local subtensor
pm2 start setup_and_run.sh --name subtensor
# tmux new-session -d -s localnet -n 'localnet'
# tmux send-keys -t localnet "bash setup_and_run.sh" C-m

# Notify the user
# echo ">> localnet.sh is running in a detached tmux session named 'localnet'"
# echo ">> You can attach to this session with: tmux attach-session -t localnet"

# Go the root
cd $ROOT