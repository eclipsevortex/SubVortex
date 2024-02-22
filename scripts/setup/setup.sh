#!/bin/bash

version=${1:-3.10.12}

# Install Python
## Install python version
pyenv install $version
echo -e "\\e[32m[pyenv] python $version installed\\e[0m"

## Default python version
pyenv global $version
echo -e "\\e[32m[pyenv] python $version configured globally\\e[0m"

# Install Bittensor
pip install bittensor
echo -e '\e[32m[bittensor] Bittensor installed\e[0m'

# 1- Install Substrate dependencies
sudo apt install --assume-yes make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler
echo -e "\\e[32mSubstrate dependencies installed\\e[0m"

# 2- Install Rust and Cargo
# Choose the default option
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
exec bash
echo -e "\\e[32mRust and Cargo installed\\e[0m"