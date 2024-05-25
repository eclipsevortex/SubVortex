#!/bin/bash

WALLET_PATH=~/.bittensor/wallets/
SUBTENSOR_NETWORK="local"

## Buidl/Run a redis instance
docker-compose down redis
docker-compose build redis
docker-compose up redis -d

Tomorow 25/05/2024
TODO: Create sudo wallet and add in the subnet subtensor that use a plain_localspec (remove --raw) instead of raw_localspec

# Build/Run a subtensor with local chain
docker-compose down subtensor
docker-compose build subtensor
docker-compose up subtensor -d

# Sleep to let time for the subtensor to be sync
sleep 5

# Get the cost of creating a subnet
lock_cost=$(btcli subnet lock_cost --subtensor.network $SUBTENSOR_NETWORK | grep 'Subnet lock cost' | awk -F'τ' '{gsub(/,/,"",$2); printf "%d\n", $2}')

# Owner
## Create wallet
./scripts/wallet/wallet_setup.sh -n localnet -t owner -a gen -k coldkey

hotkey_exist=$(find $WALLET_PATH -type f -name "owner-1-*" | wc -l)
if [ $hotkey_exist -eq 0 ]; then
    ./scripts/wallet/wallet_setup.sh -n localnet -t owner -a gen -k hotkey
else
    echo -e "\\033[37mHotkey owner-1-1 already created\\033[0m"
fi

## Get the ss58 address of the coldkey/hotkey
owner_coldkey=$(cat $WALLET_PATH/owner-1/coldkey | jq -r .ss58Address)
owner_hotkey=$(cat $WALLET_PATH/owner-1/hotkeys/owner-1-1 | jq -r .ss58Address)

## Create the subnet if not already created
netuid=$(btcli subnet list --subtensor.network $SUBTENSOR_NETWORK | awk -v pattern="$owner_coldkey" '$NF == pattern {print $1}')
if [[ -z $netuid ]]; then
    ## Get the current balance
    owner_balance=$(btcli wallet balance --wallet.path $WALLET_PATH --wallet.name owner-1 --subtensor.network $SUBTENSOR_NETWORK)
    if [[ "$owner_balance" != "No wallets found." ]]; then
        owner_balance=$(echo "$owner_balance" | awk -v pattern="$owner_coldkey" '$2 == pattern {print $(NF - 2)}' | awk -F'τ' '{gsub(/,/,"",$2); printf "%d\n", $2}')
    else
        owner_balance=0
    fi
    
    if [[ -z $owner_balance ]]; then
        owner_balance=0
    fi
    
    echo -e "\\033[37mBalance for coldkey owner-1: t$owner_balance\\033[0m"
    
    ## Faucet wallet
    if (( $(echo "$owner_balance < $lock_cost" | bc -l) )); then
        # we divide by 3 as each round faucet 3 times t100
        round_count=$(echo "scale=10; ($lock_cost - $owner_balance) / 300" | bc -l)
        round_count=$(jq -n "$round_count | ceil" | bc)
        
        ./scripts/wallet/wallet_setup.sh -n localnet -t owner -a faucet -r $round_count
    fi
    
    # Register subnet if not alread exist
    btcli subnet create \
    --wallet.name "owner-1" \
    --wallet.hotkey "owner-1-1" \
    --subtensor.network $SUBTENSOR_NETWORK \
    --no_prompt
    
    echo -e "\\033[32mSubnet has been created.\\033[0m"
else
    echo -e "\\033[37mSubnet $netuid already created.\\033[0m"
fi


# Validator
./scripts/local/local_add_validator.sh


# Miner
./scripts/local/local_add_miner.sh