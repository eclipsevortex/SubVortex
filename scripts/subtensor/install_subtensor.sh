cd ~/
apt update && apt upgrade -y
apt install nodejs npm -y
npm i -g pm2
sudo apt-get update && sudo apt-get install -y curl build-essential protobuf-compiler clang git
curl https://sh.rustup.rs/ -sSf | sh -s -- -y
source "$HOME/.cargo/env"
git clone https://github.com/opentensor/subtensor.git
cd subtensor
./scripts/init.sh
cargo build --release --features runtime-benchmarks --locked
