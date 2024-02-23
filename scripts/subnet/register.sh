#!/bin/bash

NETWORK=${1:-"local"}
CHAIN_ENDPOINT=${2:-"ws://127.0.0.1:9946"}

if [[ $NETWORK != "local" ]]; then
    CHAIN_ENDPOINT=""
fi

# Register the subnet
btcli subnet create \
 --wallet.name owner \
 --subtensor.network $NETWORK \
 --subtensor.chain_endpoint $CHAIN_ENDPOINT