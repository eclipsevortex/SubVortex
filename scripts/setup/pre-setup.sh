#!/bin/bash

apt update && apt upgrade -y

# Install tree
apt-get install -y tree
echo -e '\e[32m[tree] Tree installed\e[0m'

# Install jq
apt-get install -y jq
echo -e '\e[32m[jq] Jq installed\e[0m'

# Install bc
apt-get install -y bc
echo -e '\e[32m[jq] Bc installed\e[0m'

# Install expect
apt-get install -y expect
echo -e '\e[32m[jq] Expect installed\e[0m'

# Install npm
apt-get install -y nodejs npm
echo -e '\e[32m[npm] nodejs, npm installed\e[0m'

# Install pm2
npm install -g pm2
pm2 update
echo -e '\e[32m[pm2] Pm2 installed\e[0m'

# Install git
apt install -y git
echo -e '\e[32m[git] Git installed\e[0m'

# Install pyenv
## Required dependencies
apt-get install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
echo -e '\e[32m[pyenv] Dependencies installed\e[0m'

## Install pyenv
curl https://pyenv.run | bash
echo -e '\e[32m\e[32m[pyenv] Pyenv installed\e[0m'

# Update bashrc
cat <<'EOF' >> ~/.bashrc
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"

EOF
echo -e '\e[32m[pyenv] .bashrc updated\e[0m'

## Reload shell
source ~/.bashrc
exec bash
echo -e '\e[32m[pyenv] terminal reloaded\e[0m'