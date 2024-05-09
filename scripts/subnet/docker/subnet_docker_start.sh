#!/bin/bash

# This script install a miner or validator as docker container

show_help() {
cat << EOF
Usage: ${0##*/} [-h] -- Install a miner or validator as docker container

    -h | --help             display the help
EOF
}

OPTIONS="h"
LONGOPTIONS="help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

docker-compose build miner
