#!/bin/bash

# Define the command with common arguments
command="python3 neurons/miner.py --netuid ${NETUID} --wallet.name ${WALLET_NAME} --wallet.hotkey ${WALLET_HOTKEY} --wallet.path ${WALLET_PATH} --axon.port ${AXON_PORT} --logging.debug --miner.local"

if [ ! -z "$SUBTENSOR_NETWORK" ]; then
    command+=" --subtensor.network $SUBTENSOR_NETWORK"
    elif [ ! -z "$SUBTENSOR_CHAIN_ENDPOINT" ]; then
    command+=" --subtensor.chain_endpoint $SUBTENSOR_CHAIN_ENDPOINT"
fi

# Execute the command
exec $command