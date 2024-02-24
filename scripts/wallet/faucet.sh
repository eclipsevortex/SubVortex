#!/bin/bash

WALLET_NAME=$1
COUNT=${2:-1}
NETWORK=${3:-"local"}
CHAIN_ENDPOINT=${4:-"ws://127.0.0.1:9944"}

if [[ -z $WALLET_NAME ]]; then
    echo "The wallet name to faucet is missing"
    exit 1
fi

if [[ $NETWORK != "local" ]]; then
    CHAIN_ENDPOINT=""
fi

for ((i=1; i<=$COUNT; i++)); do
    echo "Funding $WALLET_NAME ($i/$COUNT)"
    btcli wallet faucet \
        --wallet.name $WALLET_NAME \
        --subtensor.network $NETWORK \
        --subtensor.chain_endpoint $CHAIN_ENDPOINT
done