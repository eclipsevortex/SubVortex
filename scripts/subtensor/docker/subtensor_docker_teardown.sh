#!/bin/bash

# Save the current directory
CURRENT_DIRECTORY=$(pwd)

# Go to home directory
cd $HOME

# Remove subtensor
if [ -d "subtensor" ]; then
    rm -rf subtensor
fi

echo -e '\e[32mSubtensor removed\e[0m'

# Remove blockchain
rm -rf /tmp/blockchain
echo -e '\e[32mBlockchain removed\e[0m'

# Go back to the current directory
cd $CURRENT_DIRECTORY