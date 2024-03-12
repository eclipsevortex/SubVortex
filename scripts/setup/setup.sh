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