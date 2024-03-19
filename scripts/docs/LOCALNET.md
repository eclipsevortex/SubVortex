The document explains how to install everything you need to run the subnet locally.

# Setup environment

Go to the home directory

```
cd $HOME
```

Clone the SubVortex repository

```
git clone https://github.com/eclipsevortex/SubVortex.git
```

Install the pre-requisites

```
$HOME/SubVortex/scripts/setup/pre-setup.sh
```

Setup the subnet

```
$HOME/SubVortex/scripts/setup/setup.sh
```

## Local subtensor

Setup the local subtensor

```
$HOME/SubVortex/scripts/subtensor/setup.sh
```

Start the local subtensor

```
$HOME/SubVortex/scripts/subtensor/start.sh local
```

# Subnet

Install the subnet

```
$HOME/SubVortex/scripts/subnet/setup.sh
```

Faucet the owner's wallet (need 4 round of faucet)

```
$HOME/SubVortex/scripts/wallet/faucet.sh owner 4 local ws://127.0.0.1:9946
```

Register the subnet

```
$HOME/SubVortex/scripts/subnet/register.sh local ws://127.0.0.1:9946
```

# Redis

To install redis, refer to the [Redis guide](../redis/README.md)

# Miner

Faucet the miner's wallet

```
$HOME/SubVortex/scripts/wallet/faucet.sh miner 1 local ws://127.0.0.1:9946
```

Register the miner

```
btcli subnet register \
 --netuid 1 \
 --subtensor.network local \
 --subtensor.chain_endpoint ws://127.0.0.1:9946 \
 --wallet.name miner \
 --wallet.hotkey default
```

Start the miner

```
pm2 start neurons/miner.py \
 --name miner-1 \
 --interpreter python3 -- \
 --netuid 1 \
 --subtensor.network local \
 --subtensor.chain_endpoint ws://127.0.0.1:9946 \
 --wallet.name miner \
 --wallet.hotkey default \
 --logging.debug
```

# Validator

Faucet the validator's wallet

```
$HOME/SubVortex/scripts/wallet/faucet.sh validator 1 local ws://127.0.0.1:9946
```

Register the validator

```
btcli subnet register \
 --netuid 1 \
 --subtensor.network local \
 --subtensor.chain_endpoint ws://127.0.0.1:9946 \
 --wallet.name validator \
 --wallet.hotkey default
```

Start the validator

```
pm2 start neurons/validator.py \
 --name validator-1 \
 --interpreter python3 -- \
 --netuid 1 \
 --subtensor.network local \
 --subtensor.chain_endpoint ws://127.0.0.1:9946 \
 --wallet.name validator \
 --wallet.hotkey default \
 --logging.debug
```
