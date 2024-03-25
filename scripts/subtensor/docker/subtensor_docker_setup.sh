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

# Get the latest version
git pull
echo -e '\e[32mLast version pulled\e[0m'

# Go back to the current directory
cd $CURRENT_DIRECTORY
