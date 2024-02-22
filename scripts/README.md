# Installation

In order to install everything you need for a new subnet, you have to follow the steps
- run `git clone https://github.com/Subnet-Subtensor/Subnet_S.git` - clone the repository
- run `./scripts/setup/pre-setup.sh` - install useful tools (pm2, jq, pyenv, etc)
- run `./scripts/setup/setup.sh` - install the python version expected
- run `./scripts/subtensor/setup.sh` - install the local subtensor
- run `./scripts/subnet/setup.sh` - install the subnet
- run `pm2 start ./scripts/subtensor/start.sh --name subtensor` - run in background the local subtensor
- run `./scripts/wallets.sh` - create the wallets
- get the 1000t to create a new subnet - see Owner > Mint tokens from faucet
- create the subnet - see Owner > Create a subnet
- get tao on the miner - see Miner > Mint tokens from faucet
- register the miner to the subnet - see Miner > Register
- get tao on the validator - see Validator > Mint tokens from faucet
- register the validator to the subnet - see Validator > Register

# Get list of subnet

btcli subnets list \
 --subtensor.network local \
 --subtensor.chain_endpoint ws://127.0.0.1:9946

# Get the balances

btcli wallet balance \
 --subtensor.network local \
 --subtensor.chain_endpoint ws://127.0.0.1:9946 \
 --wallet.path ~/.bittensor/wallets/

# Owner

# Create a subnet

btcli subnet create \
 --wallet.name owner \
 --subtensor.chain_endpoint ws://127.0.0.1:9946

## Mint tokens from faucet

btcli wallet faucet \
 --wallet.name owner \
 --subtensor.chain_endpoint ws://127.0.0.1:9946

# Miner

## Mint tokens from faucet

btcli wallet faucet \
 --wallet.name miner \
 --subtensor.chain_endpoint ws://127.0.0.1:9946

## Get details

btcli wallet overview \
 --wallet.name miner \
 --subtensor.chain_endpoint ws://127.0.0.1:9946

## Register

btcli subnet register \
 --netuid 1 \
 --wallet.name miner \
 --wallet.hotkey default \
 --subtensor.chain_endpoint ws://127.0.0.1:9946

## Run

pm2 start neurons/miner.py \
 --name miner-1-1 \
 --interpreter python3 -- \
 --netuid 1 \
 --subtensor.chain_endpoint ws://127.0.0.1:9946 \
 --wallet.name miner \
 --wallet.hotkey default \
 --logging.trace

## Check Incentive

btcli wallet overview \
 --wallet.name miner \
 --subtensor.chain_endpoint ws://127.0.0.1:9946

# Validator

## Mint tokens from faucet

btcli wallet faucet \
 --wallet.name validator \
 --subtensor.chain_endpoint ws://127.0.0.1:9946

## Get details

btcli wallet overview \
 --wallet.name validator \
 --subtensor.chain_endpoint ws://127.0.0.1:9946

## Register

btcli subnet register \
 --netuid 1 \
 --wallet.name validator \
 --wallet.hotkey default \
 --subtensor.chain_endpoint ws://127.0.0.1:9946

## Stake

btcli stake add \
 --wallet.name validator \
 --wallet.hotkey default \
 --subtensor.chain_endpoint ws://127.0.0.1:9946

## Run

pm2 start neurons/validator.py \
 --name validator-1-1 \
 --interpreter python3 -- \
 --netuid 1 \
 --subtensor.chain_endpoint ws://127.0.0.1:9946 \
 --wallet.name validator \
 --wallet.hotkey default \
 --logging.trace
