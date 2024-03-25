#!/bin/bash

# This script disable snapshots and enable AOF for redis

show_help() {
cat << EOF
Usage: ${0##*/} [-p ARG] [-s] [-h] -- Disable snapshots and enable AOF for redis

    -p | --port ARG         port of the redis instance, default 6379
    -s | --silent           if provided, nothing will be redirected to the ouput, false otherwise
    -h | --help             display the help
EOF
}

OPTIONS="p:sh"
LONGOPTIONS="port:,silent,:help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

REDIS_PORT=6379
SILENT=false

while [ "$#" -gt 0 ]; do
    case "$1" in
        -p | --port)
            REDIS_PORT="$2"
            shift 2
        ;;
        -s | --silent)
            SILENT=true
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

# Check if UFW is installed
if ! command -v ufw &> /dev/null; then
    echo "UFW is not installed."
    exit 1
fi

# Ensure UFW is enabled
ufw status | grep -q inactive && (echo "y" | ufw enable) &> /dev/null

# Deny all external traffic to port $REDIS_PORT
ufw deny $REDIS_PORT &> /dev/null

# Allow all local traffic to port $REDIS_PORT
ufw allow from 127.0.0.1 to any port $REDIS_PORT &> /dev/null

# Default behaviour 
# TODO: rewrite that firewall in order to avoid the following as it can be different from everyone
sudo ufw default allow incoming &> /dev/null
sudo ufw default allow outgoing &> /dev/null

# Reload UFW to apply changes
ufw reload &> /dev/null

# Notification
! $SILENT && echo -e "\\033[32mFirewall updated\\033[0m"
