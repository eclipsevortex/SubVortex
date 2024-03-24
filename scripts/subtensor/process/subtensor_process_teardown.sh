#!/bin/bash

# Remove subtensor
if [ -d "subtensor" ]; then
    rm -rf subtensor
fi

echo -e '\e[32mSubtensor removed\e[0m'

# Uninstall rust and cargo
rustup self uninstall
echo -e '\e[32mRust and Cargo uninstalled\e[0m'

# Remove rustup
rm -rf ~/.rustup
echo -e '\e[32mRustup removed\e[0m'

# Remove cargo binary
rm -rf ~/.cargo/bin
echo -e '\e[32mCargo binary removed\e[0m'

# Remove blockchain
rm -rf /tmp/blockchain
echo -e '\e[32mBlockchain removed\e[0m'