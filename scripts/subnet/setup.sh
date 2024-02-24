#!/bin/bash

ROOT=${1:-$HOME}

# Go to the repository
cd $ROOT/SubVortex

# Install speedtest-cli (needed only for the miner)
apt-get update
apt-get install speedtest-cli 

# Install the dependencies
python -m pip install -e .
echo -e "\\e[32mSubnet dependencies installed\\e[0m"

# Go back to the home directory
cd $HOME