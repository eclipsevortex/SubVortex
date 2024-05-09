#!/bin/bash

show_help() {
cat << EOF
Usage: ${0##*/} [-h] -- Manage wallet keys
    -a | --action   action you want to execute on the wallet
    -t | --type     type of wallet, owner, validator or miner
    -k | --key      type of key, coldkey or hotkey
    -n | --network  network to manage the wallet into
    -m | --name     name of the key
    -r | --round    number of round to execute the action
    -h | --help     display the help
EOF
}

OPTIONS="a:t:k:n:m:h"
LONGOPTIONS="action:,type:,key:,network:,name:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

NETWORK='mainnet'
ACTION_ROUND=1

while [ "$#" -gt 0 ]; do
    case "$1" in
        -a | --action)
            WALLET_ACTION="$2"
            shift 2
        ;;
        -t | --type)
            WALLET_TYPE="$2"
            shift 2
        ;;
        -k | --key)
            WALLET_KEY="$2"
            shift 2
        ;;
        -n | --network)
            NETWORK="$2"
            shift 2
        ;;
        -m | --name)
            WALLET_NAME="$2"
            shift 2
        ;;
        -r | --round)
            ACTION_ROUND="$2"
            shift 2
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

get_netuid() {
    if [[ "$NETWORK" == "mainnet" ]]; then
        echo 7
        elif [[ "$NETWORK" == "testnet" ]]; then
        echo 92
        elif [[ "$NETWORK" == "localnet" ]]; then
        echo 1
    else
        echo -1
    fi
}

NETUID=$(get_netuid)
WALLET_PATH=~/.bittensor/wallets

# if [[ "$WALLET_TYPE" == "root" ]]; then
#     # Manage root wallet
#     NAME=${WALLET_NAME:-root}
    
#     if [[ "$WALLET_ACTION" == "faucet" ]]; then
#         if [[ "$NETWORK" != "localnet" ]]; then
#             echo -e "\\033[31mFaucet a wallet is only available for localnet network\\033[0m"
#             exit 1
#         fi
        
#         COUNT=${ACTION_ROUND:-4}
#         for ((i=1; i<=COUNT; i++)); do
#             echo -e "\\033[37m[Round $i] Faucetting colkey $NAME-$NETUID\\033[0m"
            
#             btcli wallet faucet \
#             --wallet.name "$NAME-$NETUID" \
#             --subtensor.network local \
#             --no_prompt &> /dev/null
#         done
        
#         echo -e "\\033[32mColkey $NAME-$NETUID has been faucet\\033[0m"
#     fi
    
#     if [[ "$WALLET_ACTION" == "gen" ]]; then
#         if [[ "$WALLET_KEY" == "coldkey" ]]; then
#             OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
            
#             exist=$(find $WALLET_PATH -type d -name "$NAME-$NETUID")
#             if [[ -n $exist ]]; then
#                 echo -e "\\033[37mColdkey $NAME-$NETUID already created\\033[0m"
#                 exit 0
#             fi
            
#             btcli wallet new_coldkey --wallet.name "$NAME-$NETUID" $OPTIONS
#             echo -e "\\033[32mColdkey $NAME-$NETUID created\\033[0m"
#         fi
        
#         if [[ "$WALLET_KEY" == "hotkey" ]]; then
#             OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
            
#             hotkey_count=$(find $WALLET_PATH -type f -name "$NAME-$NETUID-*" | wc -l)
#             ((hotkey_count++))
            
#             btcli wallet new_hotkey --wallet.name "$NAME-$NETUID" --wallet.hotkey "$NAME-$NETUID-$hotkey_count" $OPTIONS
#             echo -e "\\033[32mHotkey $NAME-$NETUID-$hotkey_count created\\033[0m"
#         fi
#     fi
    
#     if [[ "$WALLET_ACTION" == "regen" ]]; then
#         if [[ "$WALLET_KEY" == "coldkey" ]]; then
#             OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
            
#             btcli wallet regen_coldkey --wallet.name "$NAME-$NETUID" $OPTIONS
#             echo -e "\\033[32mColdkey $NAME-$NETUID has been re-generated\\033[0m"
#         fi
        
#         if [[ "$WALLET_KEY" == "hotkey" ]]; then
#             OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
            
#             btcli wallet regen_hotkey --wallet.name "$NAME-$NETUID" --wallet.hotkey "$NAME-$NETUID-$hotkey_count" $OPTIONS
#             echo -e "\\033[32mHotkey $NAME-$NETUID-$hotkey_count created\\033[0m"
#         fi
#     fi
# fi

# if [[ "$WALLET_TYPE" == "owner" ]]; then
#     # Manage owner wallet
#     if [[ "$WALLET_ACTION" == "faucet" ]]; then
#         if [[ "$NETWORK" != "localnet" ]]; then
#             echo -e "\\033[31mFaucet a wallet is only available for localnet network\\033[0m"
#             exit 1
#         fi
        
#         COUNT=${ACTION_ROUND:-4}
#         for ((i=1; i<=COUNT; i++)); do
#             echo -e "\\033[37m[Round $i] Faucetting colkey owner-$NETUID\\033[0m"
            
#             btcli wallet faucet \
#             --wallet.name "owner-$NETUID" \
#             --subtensor.network local \
#             --no_prompt &> /dev/null
#         done
        
#         echo -e "\\033[32mColkey owner-$NETUID has been faucet\\033[0m"
#     fi
    
#     if [[ "$WALLET_ACTION" == "gen" ]]; then
#         if [[ "$WALLET_KEY" == "coldkey" ]]; then
#             OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
            
#             exist=$(find $WALLET_PATH -type d -name "owner-$NETUID")
#             if [[ -n $exist ]]; then
#                 echo -e "\\033[37mColdkey owner-$NETUID already created\\033[0m"
#                 exit 0
#             fi
            
#             btcli wallet new_coldkey --wallet.name "owner-$NETUID" $OPTIONS
#             echo -e "\\033[32mColdkey owner-$NETUID created\\033[0m"
#         fi
        
#         if [[ "$WALLET_KEY" == "hotkey" ]]; then
#             OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
            
#             hotkey_count=$(find $WALLET_PATH -type f -name "owner-$NETUID-*" | wc -l)
#             ((hotkey_count++))
            
#             btcli wallet new_hotkey --wallet.name "owner-$NETUID" --wallet.hotkey "owner-$NETUID-$hotkey_count" $OPTIONS
#             echo -e "\\033[32mHotkey owner-$NETUID-$hotkey_count created\\033[0m"
#         fi
#     fi
    
#     if [[ "$WALLET_ACTION" == "regen" ]]; then
#         if [[ "$WALLET_KEY" == "coldkey" ]]; then
#             OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
            
#             btcli wallet regen_coldkey --wallet.name "owner-$NETUID" $OPTIONS
#             echo -e "\\033[32mColdkey owner-$NETUID has been re-generated\\033[0m"
#         fi
        
#         if [[ "$WALLET_KEY" == "hotkey" ]]; then
#             OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
            
#             btcli wallet regen_hotkey --wallet.name "owner-$NETUID" --wallet.hotkey "owner-$NETUID-$hotkey_count" $OPTIONS
#             echo -e "\\033[32mHotkey owner-$NETUID-$hotkey_count created\\033[0m"
#         fi
#     fi
# fi

# Manage owner wallet
if [[ "$WALLET_ACTION" == "faucet" ]]; then
    if [[ "$NETWORK" != "localnet" ]]; then
        echo -e "\\033[31mFaucet a wallet is only available for localnet network\\033[0m"
        exit 1
    fi
    
    COUNT=${ACTION_ROUND:-4}
    for ((i=1; i<=COUNT; i++)); do
        echo -e "\\033[37m[Round $i] Faucetting colkey $WALLET_TYPE-$NETUID\\033[0m"
        
        btcli wallet faucet \
        --wallet.name "$WALLET_TYPE-$NETUID" \
        --subtensor.network local \
        --no_prompt &> /dev/null
    done
    
    echo -e "\\033[32mColkey $WALLET_TYPE-$NETUID has been faucet\\033[0m"
fi

if [[ "$WALLET_ACTION" == "gen" ]]; then
    if [[ "$WALLET_KEY" == "coldkey" ]]; then
        OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
        
        exist=$(find $WALLET_PATH -type d -name "$WALLET_TYPE-$NETUID")
        if [[ -n $exist ]]; then
            echo -e "\\033[37mColdkey $WALLET_TYPE-$NETUID already created\\033[0m"
            exit 0
        fi
        
        btcli wallet new_coldkey --wallet.name "$WALLET_TYPE-$NETUID" $OPTIONS
        echo -e "\\033[32mColdkey $WALLET_TYPE-$NETUID created\\033[0m"
    fi
    
    if [[ "$WALLET_KEY" == "hotkey" ]]; then
        OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
        
        hotkey_count=$(find $WALLET_PATH -type f -name "$WALLET_TYPE-$NETUID-*" | wc -l)
        ((hotkey_count++))
        
        btcli wallet new_hotkey --wallet.name "$WALLET_TYPE-$NETUID" --wallet.hotkey "$WALLET_TYPE-$NETUID-$hotkey_count" $OPTIONS
        echo -e "\\033[32mHotkey $WALLET_TYPE-$NETUID-$hotkey_count created\\033[0m"
    fi
fi

if [[ "$WALLET_ACTION" == "regen" ]]; then
    if [[ "$WALLET_KEY" == "coldkey" ]]; then
        OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
        
        btcli wallet regen_coldkey --wallet.name "$WALLET_TYPE-$NETUID" $OPTIONS
        echo -e "\\033[32mColdkey $WALLET_TYPE-$NETUID has been re-generated\\033[0m"
    fi
    
    if [[ "$WALLET_KEY" == "hotkey" ]]; then
        OPTIONS=$([[ "$NETWORK" == "localnet" ]] && echo "--no_password" || echo "")
        
        btcli wallet regen_hotkey --wallet.name "$WALLET_TYPE-$NETUID" --wallet.hotkey "$WALLET_TYPE-$NETUID-$hotkey_count" $OPTIONS
        echo -e "\\033[32mHotkey $WALLET_TYPE-$NETUID-$hotkey_count created\\033[0m"
    fi
fi

# if [[ "$WALLET_TYPE" == "validator" ]]; then
#     # Manage validator wallet
#     echo "validator"
# fi

# if [[ "$WALLET_TYPE" == "miner" ]]; then
#     # Manage miner wallet
#     echo "Miner"
# fi

# Create wallet
# btcli wallet new_coldkey --wallet.name $wallet --no_password --no_prompt

# Regenerate wallet

# Register wallet
