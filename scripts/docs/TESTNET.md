The document explain how to run miner and validator on the testnet network. 
The SubVortex has the uid **92** on the testnet network

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

# Subnet
Install the subnet
```
$HOME/SubVortex/scripts/subnet/setup.sh
```

Faucet the owner's wallet
Faucet is disabled on the testchain. Hence, if you don't have sufficient faucet tokens, ask the Bittensor Discord community for faucet tokens.

Register the subnet
```
$HOME/SubVortex/scripts/subnet/register.sh
```

# Miner
To run a miner, you have to run a local subtensor and linked it to your miner

## Install local subtensor
The binary version of the subtensor does not work and still in investigation
So we have to run it with docker

Setup the local subtensor
```
$HOME/SubVortex/scripts/subtensor/setup.sh docker
```

Start the local subtensor 
```
$HOME/SubVortex/scripts/subtensor/start.sh testnet docker
```

## Register and start miner
Faucet the miner's wallet
Faucet is disabled on the testchain. Hence, if you don't have sufficient faucet tokens, ask the Bittensor Discord community for faucet tokens.

Register the miner
```
btcli subnet register \
 --netuid 92 \
 --subtensor.network local \
 --wallet.name miner \
 --wallet.hotkey default
```

Start the miner
```
pm2 start neurons/miner.py \
 --name miner-1 \
 --interpreter python3 -- \
 --netuid 92 \
 --subtensor.network local \
 --wallet.name miner \
 --wallet.hotkey default \
 --logging.debug
```

# Validator
To run a validator, you have to install redis in order to store the metrics to compute the rewards

## Install redis
Install redis
```
$HOME/SubVortex/scripts/redis/install_redis.sh
```

Configure firewall
```
$HOME/SubVortex/scripts/redis/create_redis_firewall.sh
```

Setup password
```
$HOME/SubVortex/scripts/redis/set_redis_password.sh
```

Disable rdb
```
$HOME/SubVortex/scripts/redis/disable_rdb.sh
```

## Register and start validator
Faucet the validator's wallet
Faucet is disabled on the testchain. Hence, if you don't have sufficient faucet tokens, ask the Bittensor Discord community for faucet tokens.

Register the validator
```
btcli subnet register \
 --netuid 92 \
 --subtensor.chain_endpoint ws://<IP>:9944 \
 --wallet.name validator \
 --wallet.hotkey default
```

Start the validator
```
pm2 start neurons/validator.py \
 --name validator-1 \
 --interpreter python3 -- \
 --netuid 92 \
 --subtensor.chain_endpoint ws://<IP>:9944 \
 --wallet.name validator \
 --wallet.hotkey default \
 --logging.debug
```

<IP> will be the ip of the slocal subtensor targeting the network testnet. If it does not go against the use case you want to test you can use the local subtensor hosted by your miner




