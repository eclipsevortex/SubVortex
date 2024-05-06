#!/bin/bash

source ${BASH_SOURCE%/*}/utils/tools.sh

show_help() {
cat << EOF
Usage: ${0##*/} [-t ARG] [-n ARG] [-h] -- Install and run a miner or a validator
    -t | --type ARG         type of process you want to run (miner or validator), default miner
    -n | --network ARG      network to run the local subtensor on (e.g localnet, testnet and mainnet), default mainnet
    -s | --subtensor ARG    subtensor to use (e.g finney, test or ws://<IP>:9944), default finney. Use it only for validator. For miner it will be overrided to local as you have to have a subtensor running with the miner
    -i | --skip-setup       Skip the setup and focus only on the running
    -h | --help             display the help
EOF
}

OPTIONS="t:n:s:ih"
LONGOPTIONS="type:,network:,subtensor:,skip-setup,:help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

TYPE='miner'
NETWORK='mainnet'
SUBTENSOR='finney'
SKIP_SETUP=false

while [ "$#" -gt 0 ]; do
    case "$1" in
        -t | --type)
            TYPE="$2"
            shift 2
        ;;
        -n | --network)
            NETWORK="$2"
            shift 2
        ;;
        -s | --subtensor)
            SUBTENSOR="$2"
            shift 2
        ;;
        -i | --skip-setup)
            SKIP_SETUP=true
            shift 1
        ;;
        -h | --help)
            show_help
            exit 0
        ;;
        *)
            echo "Unrecognized option '$1'"
            exit 1
        ;;
    esac
done

# We change the default value of the subnet if testnet network is choosen
# and no subtensor is provided
if [[ $NETWORK == "testnet" ]] && [[ $SUBTENSOR == "finney" ]]; then 
    SUBTENSOR='test'
fi

# Static variables
REPOSITORY_NAME=SubVortex
NETUID=$([[ $NETWORK == "testnet" ]] && echo 92 || echo 7)

# Questions
## Check if the user want to generate or re-generate a coldkey
read -p "Do you want to (re-)generate a coldkey (yes/no)? " ACTION_ON_COLDKEY
if [ "$ACTION_ON_COLDKEY" != "yes" ] && [ "$ACTION_ON_COLDKEY" != "no" ]; then
    echo -e "\\e[31mThe possible choices are 'yes' or 'no'.\\e[0m"
    exit 1
fi

if [[ $ACTION_ON_COLDKEY == "yes" ]]; then
    read -p "Do you want to generate a new coldkey (yes/no)? " NEW_COLDKEY
    read -p "Enter the wallet name: " WALLET_NAME

    if [[ $NEW_COLDKEY == 'no' ]]; then
        read -p "Enter mnemonic, seed, or json file location for the coldkey? " COLDKEY_MNEMONIC
    fi
else
    read -p "Enter the wallet name: " WALLET_NAME
fi

## Check if the user want to generate or re-generate a hotkey
read -p "Do you want to (re-)generate a hotkey (yes/no)? " ACTION_ON_HOTKEY
if [ "$ACTION_ON_HOTKEY" != "yes" ] && [ "$ACTION_ON_HOTKEY" != "no" ]; then
    echo -e "\\e[31mThe possible choices are 'yes' or 'no'.\\e[0m"
    exit 1
fi

if [[ $ACTION_ON_HOTKEY == "yes" ]]; then
    read -p "Do you want to generate a new hotkey (yes/no)? " NEW_HOTKEY
    read -p "Enter the hotkey name: " HOTKEY_NAME

    if [[ $NEW_HOTKEY == 'no' ]]; then
        read -p "Enter mnemonic, seed, or json file location for the hotkey? " HOTKEY_MNEMONIC
    fi
else
    read -p "Enter the hotkey name: " HOTKEY_NAME
fi

## Check if the user want to register or not the hotkey to the subnet
read -p "Do you want to register to the subnet $NETUID on the network $NETWORK (yes/no)? " REGISTER
if [ "$REGISTER" != "yes" ] && [ "$REGISTER" != "no" ]; then
    echo -e "\\e[31mThe possible choices are 'yes' or 'no'.\\e[0m"
    exit 1
fi

## User want to setup and run a validator
if [[ "$TYPE" == "validator" ]]; then
    read -p "How do you want to run redis (process/docker)? " VALIDATOR_EXEC_TYPE
    
    # Check the value entered
    if [ "$VALIDATOR_EXEC_TYPE" != "process" ] && [ "$VALIDATOR_EXEC_TYPE" != "docker" ]; then
        echo -e "\\e[31mThe possible choices are 'process' or 'docker'.\\e[0m"
        exit 1
    fi

    read -p "Do you want to install wandb - it is highly recommended to expose statics to users (yes/no)? " WANDB
    
    # Check the value entered
    if [ "$WANDB" != "yes" ] && [ "$WANDB" != "no" ]; then
        echo -e "\\e[31mThe possible choices are 'yes' or 'no'.\\e[0m"
        exit 1
    fi
fi

## User want to setup and run a miner
if [[ "$TYPE" == "miner" ]]; then
    read -p "How do you want to run the local subtensor (process/docker)? " MINER_EXEC_TYPE
    
    # Check the value entered
    if [ "$MINER_EXEC_TYPE" != "process" ] && [ "$MINER_EXEC_TYPE" != "docker" ]; then
        echo -e "\\e[31mThe possible choices are 'process' or 'docker'.\\e[0m"
        exit 1
    fi
fi

# Install prerequisites
install_pm2

# Install subnet
## Install the subnet
./scripts/subnet/subnet_setup.sh

# Install redis if the user want to run a validator
if [[ "$TYPE" == "validator" ]]; then
    # Setup and run redis
    EXEC_TYPE=$([[ $VALIDATOR_EXEC_TYPE == 'docker' ]] && echo $VALIDATOR_EXEC_TYPE || echo "binary")
    ./scripts/redis/setup_and_run.sh -e $VALIDATOR_EXEC_TYPE -n $NETWORK
fi

# Install local subtensor if the user want to run a miner
if [[ "$TYPE" == "miner" ]]; then
    # Setup and run local subtensor
    ./scripts/subtensor/setup_and_run.sh -e $MINER_EXEC_TYPE -n $NETWORK
fi

# (Re-)Generate coldkey
if [[ $ACTION_ON_COLDKEY == 'yes' ]]; then
    if [[ $NEW_COLDKEY == 'yes' ]]; then
        # Generate a new coldkey
        btcli w new_coldkey --wallet.name $WALLET_NAME
    else
        # Re-generate an existing coldkey
        btcli w regen_coldkey --wallet.name $WALLET_NAME --mnemonic $COLDKEY_MNEMONIC
    fi
fi

# (Re-)Generate hotkey
if [[ $ACTION_ON_HOTKEY == 'yes' ]]; then
    if [[ $NEW_HOTKEY == 'yes' ]]; then
        # Generate a new hotkey
        btcli w new_hotkey --wallet.name $WALLET_NAME --wallet.hotkey $HOTKEY_NAME
    else
        # Re-generate an existing hotkey
        btcli w regen_hotkey --wallet.name $WALLET_NAME --wallet.hotkey $HOTKEY_NAME --mnemonic $HOTKEY_MNEMONIC
    fi
fi

if [[ $REGISTER == 'yes' ]]; then
    # Get subtensor option
    OPTIONS=$([[ "$SUBTENSOR" == "ws://"* ]] && echo "--subtensor.chain_endpoint $SUBTENSOR" || echo "--subtensor.network $SUBTENSOR")

    # Register hotkey
    btcli s register \
    --netuid $NETUID \
    --wallet.name $WALLET_NAME \
    --wallet.hotkey $HOTKEY_NAME \
    $OPTIONS
fi

# Run miner
if [[ "$TYPE" == "miner" ]]; then
    # Stop and delete miner if up and running
    process=$(pm2 list | grep "miner-$NETUID")
    if [[ ! -z $process ]]; then
        pm2 stop miner-$NETUID && pm2 delete miner-$NETUID
    fi

    # Run the miner
    pm2 start $HOME/SubVortex/neurons/miner.py \
    --name miner-$NETUID \
    --interpreter python3 -- \
    --netuid $NETUID \
    --subtensor.network local \
    --wallet.name $WALLET_NAME \
    --wallet.hotkey $HOTKEY_NAME \
    --logging.debug \
    --auto-update
fi

# Run validator
if [[ "$TYPE" == "validator" ]]; then
    # Get subtensor option
    OPTIONS=$([[ "$SUBTENSOR" == "ws://"* ]] && echo "--subtensor.chain_endpoint $SUBTENSOR" || echo "--subtensor.network $SUBTENSOR")
    OPTIONS+=$([[ "$WANDB" == "no" ]] && echo " --wandb.off" || echo "")

    # Stop and delete validator if up and running
    process=$(pm2 list | grep "validator-$NETUID" &> /dev/null;)
    if [[ ! -z $process ]]; then
        pm2 stop validator-$NETUID && pm2 delete validator-$NETUID
    fi

    # Set the redis password
    if [[ $VALIDATOR_EXEC_TYPE == "docker" ]]; then
        export REDIS_PASSWORD=$(docker exec -it subvortex-redis /bin/sh -c "grep -Eo '^requirepass[[:space:]]+(.*)$' /etc/redis/redis.conf | awk '{print \$2}'")
    fi

    # Run the validator
    pm2 start $HOME/SubVortex/neurons/validator.py -f \
    --name validator-$NETUID \
    --interpreter python3 -- \
    --netuid $NETUID \
    --wallet.name $WALLET_NAME \
    --wallet.hotkey $HOTKEY_NAME \
    --logging.debug  \
    --auto-update \
    $OPTIONS
fi
