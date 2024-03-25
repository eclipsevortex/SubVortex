#!/bin/bash

source ${BASH_SOURCE%/*}/../../utils/machine.sh

show_help() {
cat << EOF
Usage: ${0##*/} [-n ARG] [-h] -- Remove the local subtensor

    -n | --network ARG      network to run the local subtensor on (e.g localnet, testnet and mainnet), default mainnet
    -h | --help             display the help
EOF
}

OPTIONS="n:h"
LONGOPTIONS="network:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

NETWORK="mainnet"

while [ "$#" -gt 0 ]; do
    case "$1" in
        -n | --network)
            NETWORK="$2"
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

# Save the current directory
CURRENT_DIRECTORY=$(pwd)

# Go to home directory
cd $HOME/subtensor

# Stop container
docker-compose stop "$NETWORK-lite"

# Remove subtensor container and everything related
docker-compose down &> /dev/null
echo -e "\\033[32mSubtensor cleaned\\033[0m"

# Down and remove volumes
docker-compose down --volumes &> /dev/null
echo -e "\\033[32mVolumes removed\\033[0m"

# Remove subtensor container and everything related
docker-compose down --rmi all &> /dev/null
echo -e "\\033[32mImages removed\\033[0m"

# Remove subtensor
if [ -d "$HOME/subtensor" ]; then
    rm -rf $HOME/subtensor
fi

echo -e '\e[32mSubtensor removed\e[0m'

# Remove blockchain
rm -rf /tmp/blockchain
echo -e '\e[32mBlockchain removed\e[0m'

# Go back to the current directory
cd $CURRENT_DIRECTORY