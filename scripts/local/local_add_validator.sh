#!/bin/bash

INDEX=${1:-1}

WALLET_PATH=~/.bittensor/wallets/
SUBTENSOR_NETWORK="local"

## Create wallet
./scripts/wallet/wallet_setup.sh -n localnet -t validator -a gen -k coldkey

hotkey_exist=$(find $WALLET_PATH -type f -name "validator-1-$INDEX" | wc -l)
if [ $hotkey_exist -eq 0 ]; then
    ./scripts/wallet/wallet_setup.sh -n localnet -t validator -a gen -k hotkey
else
    echo -e "\\033[37mHotkey validator-1-1 already created\\033[0m"
fi

## Get the ss58 address of the coldkey/hotkey
validator_coldkey=$(cat $WALLET_PATH/validator-1/coldkey | jq -r .ss58Address)
validator_hotkey=$(cat $WALLET_PATH/validator-1/hotkeys/validator-1-$INDEX | jq -r .ss58Address)

## Get the min stake
min_state=$(python3 scripts/subnet/utils/subnet_get_min_stake.py --netuid 1 --subtensor.network $SUBTENSOR_NETWORK | grep -o 'get_weights_min_stake() [0-9]*' | awk '{print $2}')

## Get the burn_cost
burn=$(python3 scripts/subnet/utils/subnet_get_burn.py --netuid 1 --subtensor.network $SUBTENSOR_NETWORK | grep -o 'get_burn() [0-9]*' | awk '{print $2}')

# Compute the minimum balance a validator need to have
min_balance=$(echo "$min_state + $burn" | bc)

## Get the current balance
validator_balance=$(btcli wallet balance --wallet.path $WALLET_PATH --wallet.name validator-1 --subtensor.network $SUBTENSOR_NETWORK)
if [[ "$validator_balance" != "No wallets found." ]]; then
    validator_balance=$(echo "$validator_balance" | awk -v pattern="$validator_coldkey" '$2 == pattern {print $(NF - 2)}' | awk -F'τ' '{gsub(/,/,"",$2); printf "%d\n", $2}')
else
    validator_balance=0
fi

if [[ -z $validator_balance ]]; then
    validator_balance=0
fi

echo -e "\\033[37mBalance for coldkey validator-1: t$validator_balance\\033[0m"

## Faucet wallet
if (( $(echo "$validator_balance < $min_balance" | bc -l) )); then
    # we divide by 3 as each round faucet 3 times t100
    round_count=$(echo "scale=10; ($min_balance - $validator_balance) / 100" | bc -l)
    round_count=$(jq -n "$round_count | ceil" | bc)
    
    ./scripts/wallet/wallet_setup.sh -n localnet -t validator -a faucet -r $round_count
fi

## Register validator
is_registered=$(python3 scripts/subnet/utils/subnet_is_hotkey_registered.py --netuid 1 --subtensor.network $SUBTENSOR_NETWORK --wallet.name validator-1 --wallet.hotkey validator-1-$INDEX | grep -o 'is_hotkey_registered() \(False\|True\)' | awk '{print $2}')
if [[ "$is_registered" == "False" ]]; then
    btcli subnet register \
    --netuid 1 \
    --subtensor.network $SUBTENSOR_NETWORK \
    --wallet.name validator-1 \
    --wallet.hotkey validator-1-$INDEX \
    --no_prompt
    
    echo -e "\\033[32mHotkey validator-1-1 has been registered.\\033[0m"
else
    echo -e "\\033[37mHotkey validator-1-1 already registered\\033[0m"
fi

## Build/Run validator
docker-compose down validator-$INDEX
docker-compose build validator-$INDEX
docker-compose up validator-$INDEX -d