#!/bin/bash

# This script check redis is healthy

show_help() {
cat << EOF
Usage: ${0##*/} [-a ARG] [-h] -- Check redis is healthy

    -a | --password ARG     password to protect redis instance
    -h | --help             display the help
EOF
}

OPTIONS="a:h"
LONGOPTIONS="password:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

REDIS_PASSWORD=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        -a | --password)
            REDIS_PASSWORD="$2"
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

if [[ -z $REDIS_PASSWORD ]]; then
    echo -e "\\033[31mThe redis password is missing. Run with -h to display the help.\\033[0m"
    exit 1
fi

# To expose the password in docker
export REDIS_PASSWORD=$REDIS_PASSWORD

# Check redis is up and running 
result=$(echo -e "AUTH $REDIS_PASSWORD\nping" | redis-cli)
if [[ $result == *"PONG"* ]]; then
    echo -e "\\033[32mRedis is up and running\\033[0m"
else
    echo -e "\\033[31mRedis failed: $result\\033[0m"
fi