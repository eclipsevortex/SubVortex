#!/bin/bash

# Define the faucet command
COMMAND="btcli wallet faucet --wallet.name"

# Define the chain endpoint (local testnet node)
CHAIN_ENDPOINT="ws://127.0.0.1:9946"

# Define the number of times to run the command for each wallet by name
OWNER_COUNT=4
MINER_COUNT=1
VALIDATOR_COUNT=1

# Function to run the command for a specific wallet
function fund_wallet {
    wallet_name=$1
    count=$2

    for ((i=1; i<=$count; i++)); do
        echo "Funding $wallet_name ($i/$count)"
        $COMMAND $wallet_name --subtensor.chain_endpoint $CHAIN_ENDPOINT
        sleep 2  # Add a 2-second pause
    done
}

# Fund each wallet 
fund_wallet "owner" $OWNER_COUNT
fund_wallet "miner" $MINER_COUNT
fund_wallet "validator" $VALIDATOR_COUNT

echo "Funding complete." 