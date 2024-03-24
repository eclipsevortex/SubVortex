#!/bin/bash

# Go to SubVortex directory
cd SubVortex

# Uninstall subnet dependencies
xargs -r -a requirements.txt pip uninstall -y
echo -e "\\e[32mSubnet dependencies uninstalled\\e[0m"

# Go toparent
cd ../

# Remove the subnet directory
if [ -d "SubVortex" ]; then
    rm -rf SubVortex
    echo -e "\\e[32mSubnet removed\\e[0m"
else
    echo -e "\\e[38;5;208mSubnet already removed\\e[0m"
fi