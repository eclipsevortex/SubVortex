#!/bin/bash

# Section 1: Build/Install
# This section is for first-time setup and installations.

install_dependencies() {
    # Function to install packages on macOS
    install_mac() {
        which brew > /dev/null
        if [ $? -ne 0 ]; then
            echo "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        echo "Updating Homebrew packages..."
        brew update
        echo "Installing required packages..."
        brew install make llvm curl libssl protobuf tmux
    }

    # Function to install packages on Ubuntu/Debian
    install_ubuntu() {
        echo "Updating system packages..."
        sudo apt update
        echo "Installing required packages..."
        sudo apt install --assume-yes make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler tmux
    }

    # Detect OS and call the appropriate function
    if [[ "$OSTYPE" == "darwin"* ]]; then
        install_mac
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        install_ubuntu
    else
        echo "Unsupported operating system."
        exit 1
    fi

    # Install rust and cargo
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

    # Update your shell's source to include Cargo's path
    source "$HOME/.cargo/env"
}

# Call install_dependencies only if it's the first time running the script
if [ ! -f ".dependencies_installed" ]; then
    install_dependencies
    touch .dependencies_installed
fi

# Section 2: Test/Run
# This section is for running and testing the setup.

# Create a coldkey for the owner role
wallet=${1:-owner}

# Function to run the command for a specific wallet
fund_wallet() {
    wallet_name=$1
    count=$2

    for ((i=1; i<=$count; i++)); do
        echo "Funding $wallet_name ($i/$count)"
        btcli wallet faucet \
            --wallet.name $wallet_name \
            --subtensor.chain_endpoint ws://127.0.0.1:9946 \
            --no_prompt
        sleep 2  # Add a 2-second pause
    done
}

# Logic for setting up and running the environment
setup_environment() {
    # Clone subtensor and enter the directory
    if [ ! -d "subtensor" ]; then
        git clone https://github.com/opentensor/subtensor.git
    fi

    # Go the repository
    cd subtensor

    # Get the latest version
    git pull

    # Setup rust
    ./scripts/init.sh

    # Go to the subnet
    cd ../SubVortex

    # Install depenencies
    python -m pip install -e .

    # Create and set up wallets
    # This section can be skipped if wallets are already set up
    if [ ! -f ".wallets_setup" ]; then
        btcli wallet new_coldkey --wallet.name $wallet --no_password --no_prompt
        btcli wallet new_coldkey --wallet.name miner --no_password --no_prompt
        btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default --no_prompt
        btcli wallet new_coldkey --wallet.name validator --no_password --no_prompt
        btcli wallet new_hotkey --wallet.name validator --wallet.hotkey default --no_prompt
        touch .wallets_setup
    fi

}

# Call setup_environment every time
setup_environment 

## Setup localnet
# assumes we are in the bittensor-subnet-template/ directory
# Initialize your local subtensor chain in development mode. This command will set up and run a local subtensor network.
cd ../subtensor

# Start a new tmux session and create a new pane, but do not switch to it
echo "FEATURES='pow-faucet runtime-benchmarks' BT_DEFAULT_TOKEN_WALLET=$(cat ~/.bittensor/wallets/$wallet/coldkeypub.txt | grep -oP '"ss58Address": "\K[^"]+') bash scripts/localnet.sh" >> setup_and_run.sh
chmod +x setup_and_run.sh
tmux new-session -d -s localnet -n 'localnet'
tmux send-keys -t localnet 'bash ../subtensor/setup_and_run.sh' C-m

# Notify the user
echo ">> localnet.sh is running in a detached tmux session named 'localnet'"
echo ">> You can attach to this session with: tmux attach-session -t localnet"

# Faucet the owner coldkey
fund_wallet "owner" 4

# Register a subnet (this needs to be run each time we start a new local chain)
btcli subnet create --wallet.name $wallet --wallet.hotkey default --subtensor.network local --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt

# Faucet miner/validator coldkey
fund_wallet "miner" 1
fund_wallet "validator" 4

# Register wallet hotkeys to subnet
btcli subnet register --wallet.name miner --netuid 1 --wallet.hotkey default --subtensor.network local --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt
btcli subnet register --wallet.name validator --netuid 1 --wallet.hotkey default --subtensor.network local --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt

# Add stake to the validator
btcli stake add --wallet.name validator --wallet.hotkey default --subtensor.network local --subtensor.chain_endpoint ws://127.0.0.1:9946 --amount 10000 --no_prompt

# Ensure both the miner and validator keys are successfully registered.
btcli subnet list --subtensor.network local --subtensor.chain_endpoint ws://127.0.0.1:9946
btcli wallet overview --wallet.name validator --subtensor.network local --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt
btcli wallet overview --wallet.name miner --subtensor.network local --subtensor.chain_endpoint ws://127.0.0.1:9946 --no_prompt

cd ../SubVortex

# Check if inside a tmux session
if [ -z "$TMUX" ]; then
    # Start a new tmux session and run the miner in the first pane
    tmux new-session -d -s bittensor -n 'miner' 'python neurons/miner.py --netuid 1 --subtensor.network local --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name miner --wallet.hotkey default --logging.debug'
    
    # Split the window and run the validator in the new pane
    tmux split-window -h -t bittensor:miner 'python neurons/validator.py --netuid 1 --subtensor.network local --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name validator --wallet.hotkey default --logging.debug'
    
    # Attach to the new tmux session
    tmux attach-session -t bittensor
else
    # If already in a tmux session, create two panes in the current window
    tmux split-window -h 'python neurons/miner.py --netuid 1 --subtensor.network local --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name miner --wallet.hotkey default --logging.debug'
    tmux split-window -v -t 0 'python neurons/validator.py --netuid 1 --subtensor.network local --subtensor.chain_endpoint ws://127.0.0.1:9946 --wallet.name3 validator --wallet.hotkey default --logging.debug'
fi
