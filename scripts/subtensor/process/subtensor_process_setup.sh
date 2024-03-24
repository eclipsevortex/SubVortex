#!/bin/bash

source ${BASH_SOURCE%/*}/../../utils/machine.sh

show_help() {
cat << EOF
Usage: ${0##*/} [-n ARG] [-h] -- Install the subtensor as binary

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

function install_macos_dependencies(){
    # Check brew is install
    which brew > /dev/null
    if [ $? -ne 0 ]; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
    fi
    
    # Update brew packages
    brew update

    # Install dependencies    
    brew install make llvm curl libssl protobuf
    echo -e '\e[32mBrew dependencies installed[0m'
}

function install_linux_dependencies() {
    # Update the list of packages
    apt-get update

    # Necessary libraries for Rust execution
    apt-get install -y curl build-essential protobuf-compiler clang git
    rm -rf /var/lib/apt/lists/*
    echo -e '\e[32mRust dependencies installed\e[0m'
}

os=$(get_os)

# Install dependencies
if [[ $os == "linux" ]]; then
    install_linux_dependencies
else
    install_macos_dependencies
fi

# Install rust and cargo
curl https://sh.rustup.rs -sSf | sh -s -- -y
echo -e '\e[32mRust and Cargo installed\e[0m'

# Update your shell's source to include Cargo's path
source "$HOME/.cargo/env"
echo -e '\e[32mRust and Cargo added to the path\e[0m'

# Clone subtensor and enter the directory
if [ ! -d "subtensor" ]; then
    git clone https://github.com/opentensor/subtensor.git
    echo -e '\e[32mRepository cloned\e[0m'
fi

# Go the repository
cd subtensor

# Get the latest version
git pull
echo -e '\e[32mLast version pulled\e[0m'

# Setup subtensor
./scripts/init.sh
echo -e '\e[32mWASM buils environment initialized\e[0m'

# Compile the subtensor binary
if [[ $NETWORK == "testnet" ]]; then
    echo "Compiling subtensor on network $NETWORK..."
    cargo build --release --features pow-faucet --features runtime-benchmarks --locked
    echo -e "\e[32mSubtensor on network $NETWORK is compiled\e[0m"
    elif [[ $NETWORK == "mainnet" ]]; then
    echo "Compiling subtensor on network $NETWORK..."
    cargo build --release --features runtime-benchmarks --locked
    echo -e "\e[32mSubtensor on network $NETWORK is compiled\e[0m"
fi