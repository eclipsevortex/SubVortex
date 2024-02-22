#!/bin/bash

# Go to the repository
cd $HOME/Subnet_S

# Install the dependencies
python -m pip install -e .
echo -e "\\e[32mSubnet dependencies installed\\e[0m"

# Go back to the home directory
cd $HOME