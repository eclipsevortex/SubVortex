#!/bin/bash

WALLET_PATH=~/.bittensor/wallets/

# # Build and run a subtensor with local note
# docker-compose build subtensor
# docker-compose up subtensor -d

# Get the cost of creating a subnet
lock_cost=$(btcli subnet lock_cost --subtensor.network local | awk -F'τ' '{gsub(/,/,"",$2); printf "%d\n", $2}')

# # Root
# ## Create the wallet
# ./scripts/wallet/wallet_setup.sh -n localnet -t root -a gen -k coldkey

# hotkey_exist=$(find $WALLET_PATH -type f -name "root-1-*" | wc -l)
# if [ $hotkey_exist -eq 0 ]; then
#     ./scripts/wallet/wallet_setup.sh -n localnet -t root -a gen -k hotkey
# else
#     echo -e "\\033[37mHotkey root-1-1 already created\\033[0m"
# fi

# ## Get the ss58 address of the hotkey
# root_coldkey=$(cat $WALLET_PATH/root-1/coldkey | jq -r .ss58Address)
# root_hotkey=$(cat $WALLET_PATH/root-1/hotkeys/root-1-1 | jq -r .ss58Address)

# ## Get the root uid if exists otherwise create the root validator
# rootuid=$(btcli root list --subtensor.network local | awk -v pattern="$root_hotkey" '$2 == pattern {print $1}')
# if [[ -z $rootuid ]]; then
#     ## Get the current balance
#     root_balance=$(btcli wallet balance --wallet.path $WALLET_PATH --wallet.name root-1 --subtensor.network local)
#     if [[ "$root_balance" != "No wallets found." ]]; then
#         root_balance=$(echo "$root_balance" | awk -v pattern="$root_coldkey" '$2 == pattern {print $(NF - 2)}' | awk -F'τ' '{gsub(/,/,"",$2); printf "%d\n", $2}')
#     else
#         root_balance=0
#     fi
#     echo -e "\\033[37mBalance for coldkey root-1: t$root_balance\\033[0m"
    
#     ## Faucet wallet
#     if [[ $root_balance -lt 100 ]]; then
#         ./scripts/wallet/wallet_setup.sh -n localnet -t root -a faucet -r 1
#     fi
    
#     # Register root if not alread exist
#     btcli root register \
#     --wallet.name root-1 \
#     --wallet.hotkey root-1-1 \
#     --wallet.path $WALLET_PATH \
#     --subtensor.network local \
#     --no_prompt
#     echo -e "\\033[32mRoot validator $rootuid has been created.\\033[0m"
# else
#     echo -e "\\033[37mRoot validator $rootuid already created.\\033[0m"
# fi

# secret_seed=$(docker exec -it subvortex-subnet ./target/release/node-subtensor key inspect //Alice --output-type json | jq -r .secretSeed)
# echo "Alive secret seed $secret_seed"

# btcli wallet regen_coldkey --wallet.name alice --wallet.path $WALLET_PATH --seed $secret_seed -subtensor.network local --no_password --overwrite_coldkey
# btcli wallet new_hotkey --wallet.name alice  --wallet.path $WALLET_PATH --wallet.hotkey alice-1 --subtensor.network local 

# # Owner
# ## Create wallet
# ./scripts/wallet/wallet_setup.sh -n localnet -t owner -a gen -k coldkey

# hotkey_exist=$(find $WALLET_PATH -type f -name "owner-1-*" | wc -l)
# if [ $hotkey_exist -eq 0 ]; then
#     ./scripts/wallet/wallet_setup.sh -n localnet -t owner -a gen -k hotkey
# else
#     echo -e "\\033[37mHotkey owner-1-1 already created\\033[0m"
# fi

# ## Get the ss58 address of the coldkey/hotkey
# owner_coldkey=$(cat $WALLET_PATH/owner-1/coldkey | jq -r .ss58Address)
# owner_hotkey=$(cat $WALLET_PATH/owner-1/hotkeys/owner-1-1 | jq -r .ss58Address)

# ## Get the subnet uid if exists otherwise create the subnet
# netuid=$(btcli subnet list --subtensor.network local | awk -v pattern="$owner_coldkey" '$NF == pattern {print $1}')
# if [[ -z $netuid ]]; then
#     ## Get the current balance
#     owner_balance=$(btcli wallet balance --wallet.path $WALLET_PATH --wallet.name owner-1 --subtensor.network local)
#     if [[ "$owner_balance" != "No wallets found." ]]; then
#         owner_balance=$(echo "$owner_balance" | awk -v pattern="$owner_coldkey" '$2 == pattern {print $(NF - 2)}' | awk -F'τ' '{gsub(/,/,"",$2); printf "%d\n", $2}')
#     else
#         owner_balance=0
#     fi
#     echo -e "\\033[37mBalance for coldkey owner-1: t$owner_balance\\033[0m"
    
#     ## Faucet wallet
#     if [[ -z $netuid ]] && [[ $owner_balance -lt $lock_cost ]]; then
#         # we divide by 3 as each round faucet 3 times t100
#         round_count=$(echo "scale=0; ($lock_cost - $owner_balance) / 100" | bc -l)
        
#         ./scripts/wallet/wallet_setup.sh -n localnet -t owner -a faucet -r $round_count
#     fi
    
#     # Register subnet if not alread exist
#     btcli subnet create \
#     --wallet.name "owner-1" \
#     --wallet.hotkey "owner-1-1" \
#     --subtensor.network local \
#     --no_prompt
    
#     # netuid=$(btcli subnet list --subtensor.network local | awk -v pattern="$owner_hotkey" '$NF == pattern {print $1}')
#     echo -e "\\033[32mSubnet $netuid has been created.\\033[0m"
# else
#     echo -e "\\033[37mSubnet $netuid already created.\\033[0m"
# fi

## Set subnet hyperparameters (MaxAllowedUidsSet to be 5)


# Validator

# Miner

# Stop containers
# docker stop subvortex-subnet

# Remove containers
# docker rm subvortex-subnet

