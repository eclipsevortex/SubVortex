#!/bin/bash

INDEX=${1:-1}

WALLET_PATH=~/.bittensor/wallets/
SUBTENSOR_NETWORK="local"

# Miner
## Create wallet
./scripts/wallet/wallet_setup.sh -n localnet -t miner -a gen -k coldkey

hotkey_exist=$(find $WALLET_PATH -type f -name "miner-1-$INDEX" | wc -l)
if [ $hotkey_exist -eq 0 ]; then
    ./scripts/wallet/wallet_setup.sh -n localnet -t miner -a gen -k hotkey
else
    echo -e "\\033[37mHotkey miner-1-$INDEX already created\\033[0m"
fi

## Get the ss58 address of the coldkey/hotkey
miner_coldkey=$(cat $WALLET_PATH/miner-1/coldkey | jq -r .ss58Address)
miner_hotkey=$(cat $WALLET_PATH/miner-1/hotkeys/miner-1-$INDEX | jq -r .ss58Address)

## Get the burn_cost
burn=$(python3 scripts/subnet/utils/subnet_get_burn.py --netuid 1 --subtensor.network $SUBTENSOR_NETWORK | grep -o 'get_burn() [0-9]*' | awk '{print $2}')

## Get the current balance
miner_balance=$(btcli wallet balance --wallet.path $WALLET_PATH --wallet.name miner-1 --subtensor.network $SUBTENSOR_NETWORK)
if [[ "$miner_balance" != "No wallets found." ]]; then
    miner_balance=$(echo "$miner_balance" | awk -v pattern="$miner_coldkey" '$2 == pattern {print $(NF - 2)}' | awk -F'τ' '{gsub(/,/,"",$2); printf "%d\n", $2}')
else
    miner_balance=0
fi

if [[ -z $miner_balance ]]; then
    miner_balance=0
fi

echo -e "\\033[37mBalance for coldkey miner-1: t$miner_balance\\033[0m"

## Faucet wallet
if (( $(echo "$miner_balance < $burn" | bc -l) )); then
    # we divide by 3 as each round faucet 3 times t100
    round_count=$(echo "scale=10; ($burn - $miner_balance) / 100" | bc -l)
    round_count=$(jq -n "$round_count | ceil" | bc)
    
    ./scripts/wallet/wallet_setup.sh -n localnet -t miner -a faucet -r $round_count
fi

## Register miner
is_registered=$(python3 scripts/subnet/utils/subnet_is_hotkey_registered.py --netuid 1 --subtensor.network $SUBTENSOR_NETWORK --wallet.name miner-1 --wallet.hotkey miner-1-$INDEX | grep -o 'is_hotkey_registered() \(False\|True\)' | awk '{print $2}')
if [[ "$is_registered" == "False" ]]; then
    btcli subnet register \
    --netuid 1 \
    --subtensor.network $SUBTENSOR_NETWORK \
    --wallet.name miner-1 \
    --wallet.hotkey miner-1-$INDEX \
    --no_prompt
    
    echo -e "\\033[32mHotkey miner-1-$INDEX has been registered.\\033[0m"
else
    echo -e "\\033[37mHotkey miner-1-$INDEX already registered\\033[0m"
fi

# Get the subtensor node id
subtensor_node_id=$(python3 scripts/subtensor/utils/subtensor_get_bootnode.py --subtensor.network $SUBTENSOR_NETWORK | grep -o 'get_bootnode() [^ ]*' | awk '{print $2}')

## Build/Run miner
docker-compose down miner-$INDEX
docker-compose build --build-arg SUBTENSOR_NODE_ID="$subtensor_node_id" miner-$INDEX
docker-compose up miner-$INDEX -d