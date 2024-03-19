#!/bin/bash

NETWORK=${1:-"mainnet"}
EXEC_TYPE=${2:-"binary"}
ROOT=${3:-$HOME}

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
        brew install make llvm curl libssl protobuf
    }

    # Function to install packages on Ubuntu/Debian
    install_ubuntu() {
        # Update the list of packages
        apt-get update

        if [[ "$EXEC_TYPE" == "docker" ]]; then
            # Install docker
            ## Install Required Dependencies
            sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            
            ## Add Docker's GPG Key:
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            
            ## Set up the Stable Docker Repository:
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            ## Install Docker Engine
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io
            echo -e '\e[32m[docker] Docker installed\e[0m'
            
            ## Add the user to the docker group
            sudo usermod -aG docker $USER
            echo -e '\e[32m[docker] Docker user created\e[0m'

            ## Apply the group membership (you may need to log out and log back in for the group to be recognized):
            newgrp docker
            echo -e '\e[32m[docker] Group membership applied\e[0m'
            
            # Install docker compose
            sudo apt-get install -y docker-compose
            echo -e '\e[32m[docker] Docker compose installed\e[0m'
        fi
       
        # Necessary libraries for Rust execution
        apt-get install -y curl build-essential protobuf-compiler clang git
        rm -rf /var/lib/apt/lists/*
        echo -e '\e[32mRust dependencies installed\e[0m'
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
    curl https://sh.rustup.rs -sSf | sh -s -- -y
    echo -e '\e[32mRust and Cargo installed\e[0m'

    # Update your shell's source to include Cargo's path
    source "$HOME/.cargo/env"
    echo -e '\e[32mRust and Cargo added to the path\e[0m'
}

setup_environment() {
    # Go to the root
    cd $ROOT

    # Clone subtensor and enter the directory
    if [ ! -d "subtensor" ]; then
        git clone https://github.com/opentensor/subtensor.git
        echo -e '\e[32m[Subtensor] Repository cloned\e[0m'
    fi

    # Go the repository
    cd $ROOT/subtensor

    # Get the latest version
    git pull
    echo -e '\e[32m[Subtensor] Last version pulled\e[0m'

    # Setup rust
    ./scripts/init.sh
    echo -e '\e[32m[Subtensor] Setup done\e[0m'

    # Compile the subtensor binary if needed
    if [[ "$EXEC_TYPE" == "binary" ]]; then
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

        # for localnet it is built in the script provided by subtensor
        # reference: scripts/localnet.sh
    fi

    # Go back 
    cd $ROOT
}

# Install dependencies
install_dependencies
echo -e '\e[32m[Subtensor] Dependencies installed\e[0m'


# Setup environment
setup_environment 
echo -e '\e[32m[Subtensor] Environment setup\e[0m'