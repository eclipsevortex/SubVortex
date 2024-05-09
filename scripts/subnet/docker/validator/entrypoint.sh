#!/bin/bash

# Define the command with common arguments
command="python3 neurons/validator.py --netuid ${NETUID} --wallet.name ${WALLET_NAME} --wallet.hotkey ${WALLET_HOTKEY} --wallet.path ${WALLET_PATH} --axon.port ${AXON_PORT} --database.host subvortex-redis --database.index ${DABASE_INDEX} --logging.debug --wandb.off"

if [ ! -z "$SUBTENSOR_NETWORK" ]; then
    command+=" --subtensor.network $SUBTENSOR_NETWORK"
    elif [ ! -z "$SUBTENSOR_CHAIN_ENDPOINT" ]; then
    command+=" --subtensor.chain_endpoint $SUBTENSOR_CHAIN_ENDPOINT"
fi

# Execute the command
exec $command