#!/bin/bash

# Update package manager
apt-get update

# Install the dependencies
pip install -r requirements.txt
echo -e "\\e[32mSubnet dependencies installed\\e[0m"

# Install the source
pip install -e .
echo -e "\\e[32mSubnet source installed\\e[0m"