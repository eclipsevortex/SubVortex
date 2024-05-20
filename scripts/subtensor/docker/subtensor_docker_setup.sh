#!/bin/bash

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

# Copy overrides
cp -f $HOME/SubVortex/scripts/subtensor/overrides/docker-compose.yml .

# Go back to the current directory
cd $CURRENT_DIRECTORY
