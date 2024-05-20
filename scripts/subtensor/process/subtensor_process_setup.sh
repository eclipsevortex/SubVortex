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
    apt install build-essential
    apt-get install clang curl git make
    apt install --assume-yes git clang curl libssl-dev protobuf-compiler
    apt install --assume-yes git clang curl libssl-dev llvm libudev-dev make protobuf-compiler
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
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
echo -e '\e[32mRust and Cargo installed\e[0m'

# Update your shell's source to include Cargo's path
source "$HOME/.cargo/env"
echo -e '\e[32mRust and Cargo added to the path\e[0m'

# Save the current directory
CURRENT_DIRECTORY=$(pwd)

# Go to home directory
cd $HOME

# Clone subtensor and enter the directory
if [ ! -d "subtensor" ]; then
    git clone https://github.com/opentensor/subtensor.git
    echo -e '\e[32mRepository cloned\e[0m'
fi

# Go the repository
cd subtensor

# Checkout main branch
git checkout main
echo -e '\e[32mCheckout main branch\e[0m'

# Remove previous chain state:
rm -rf /tmp/blockchain 
echo -e '\e[32mRemove chain state\e[0m'

# Get the latest version
git pull origin main
echo -e '\e[32mLast version pulled\e[0m'

# Install Rust toolchain
rustup default stable
rustup update
rustup target add wasm32-unknown-unknown
rustup toolchain install nightly
rustup target add --toolchain nightly wasm32-unknown-unknown
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

# Go back to the current directory
cd $CURRENT_DIRECTORY