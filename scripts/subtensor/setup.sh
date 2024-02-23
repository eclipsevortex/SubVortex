#!/bin/bash

ROOT=${1:-$HOME}

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
        sudo apt install --assume-yes make build-essential clang libssl-dev llvm libudev-dev protobuf-compiler
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

setup_environment() {
    # Clone subtensor and enter the directory
    if [ ! -d "subtensor" ]; then
        git clone https://github.com/opentensor/subtensor.git
    fi

    # Go the repository
    cd $ROOT/subtensor

    # Get the latest version
    git pull

    # Setup rust
    ./scripts/init.sh

    # Go back 
    cd $ROOT
}

# Call setup_environment every time
setup_environment 