#!/bin/bash

# This script setup and run a redis instance
# TODO: check the valud for each argument is an expected one

source ${BASH_SOURCE%/*}/../utils/tools.sh

show_help() {
cat << EOF
Usage: ${0##*/} [-e ARG] [-n ARG] [-h] -- Install and run redis

    -e | --exec ARG      type of execution of the redis instance (binary or docker), default docker
    -n | --network ARG   network to run the local subtensor on (e.g localnet, testnet and mainnet), default mainnet
    -h | --help          display the help
EOF
}

OPTIONS="e:n:h"
LONGOPTIONS="exec:,network:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

EXEC_TYPE='docker'
NETWORK='mainnet'

while [ "$#" -gt 0 ]; do
    case "$1" in
        -e | --exec)
            EXEC_TYPE="$2"
            shift 2
        ;;
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

# Get the base path
current_dir=$(pwd)
relative_dir="SubVortex/scripts/redis"
if [[ $current_dir != *"SubVortex"* ]]; then
    BASE="${current_dir%/}/${relative_dir%/}"
else
    BASE="${current_dir%/}/${relative_dir#*/}"
fi

# Install docker if needed
if [[ "$EXEC_TYPE" == "docker" ]]; then
    $BASE/../docker/docker_setup.sh
    echo -e "\\033[32mDocker setup\\033[0m"
fi

# Setup redis
if [[ $EXEC_TYPE == 'docker' ]]; then
    PASSWORD=$($BASE/docker/redis_docker_setup.sh -s)
else
    if [[ $EXEC_TYPE == "process" ]]; then
        install_pm2
    fi

    $BASE/process/redis_process_setup.sh
    PASSWORD=$(sudo grep -Po '^requirepass \K.*' /etc/redis/redis.conf)
fi
echo -e "\\033[32mRedis setup\\033[0m"

# Start redis
$BASE/$EXEC_TYPE/redis_"$EXEC_TYPE"_start.sh -a "$PASSWORD"

# Health Check
$BASE/$EXEC_TYPE/redis_"$EXEC_TYPE"_health_check.sh -a "$PASSWORD"