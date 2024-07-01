#!/bin/bash

show_help() {
cat << EOF
Usage: ${0##*/} [-t ARG] [-h] -- Install os packages for miner or validator
    -t | --type ARG         type of process you want to run (miner or validator), default miner
    -h | --help             display the help
EOF
}

OPTIONS="t:ih"
LONGOPTIONS="type:,:help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

TYPE='miner'

while [ "$#" -gt 0 ]; do
    case "$1" in
        -t | --type)
            TYPE="$2"
            shift 2
        ;;
        *)
            echo "Unrecognized option '$1'"
            exit 1
        ;;
    esac
done

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

is_package_installed() {
    dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -c "ok installed"
}

install_package() {
    local package_name=$1
    
    if [ $(is_package_installed "$package_name") -eq 0 ]; then
        sudo apt-get install -y "$package_name"
        if [ $(is_package_installed "$package_name") -eq 1 ]; then
            echo -e "\\e[32m$package_name installed\\e[0m"
        else
            echo -e "\\e[31m$package_name installation failed\\e[0m"
        fi
    fi
}

# Update package manager
apt-get update

# Install common packages
install_package "git"
install_package "python3-pip"

# Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [[ "$TYPE" == "miner" ]]; then
        # Dependencies to use nfqueue
        install_package "build-essential"
        install_package "python3-dev"
        install_package "libnetfilter-queue-dev"
    fi
fi

# Macos
# if [[ "$OSTYPE" == "darwin"* ]]; then

# fi

# Window
# if [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
# fi
