<div align="center">

# **SubVortex** <!-- omit in toc -->

[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/bittensor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## An Incentivized and Decentralized Subtensor Network <!-- omit in toc -->

[Discord](https://discord.gg/bittensor) • [Network](https://taostats.io/) • [Research](https://bittensor.com/whitepaper)

---

<div>
  <img src="subvortex.png" alt="Image Description" width="300" height="300">
</div>
<br />
<div style="font-size: 20px">Testnet: 92 • Mainnet: TBD</div>

</div>

---

- [Abstract](#abstract)
- [Introduction](#introduction)
- [Goals](#goals)
- [Roles](#roles)
- [Subtensor & Bittensor](#subtensor--bittensor)
- [Incentive Mechanism](#incentive-mechanism)
- [Value Proposition](#value-proposition)
- [Team Composition](#team-composition)
- [Road Map](#road-map)
- [Conclusion](#conclusion)
- [Installation](#installation)
  - [Install SubVortex](#install-subvortex)
  - [Install Subtensor](#install-local-subtensor)
  - [Install Redis](#install-redis)
- [Registering your wallet](#registering-your-wallet)
- [Running a Miner](#running-a-miner)
- [Running a Validator](#running-a-validator)
- [New Releases](#new-releases)
- [Troubleshooting](#troubleshooting)
  - [Troubleshooting Subtensor](#troubleshooting-subtensor) 
- [License](#license)

## Abstract

SubVortex introduces an incentivized and decentralized network of subtensor nodes which are a pivotal element within the Bittensor ecosystem. This delineates the structure, objectives, and mechanisms of SubVortex, aiming to foster decentralization, stability, and efficient resource allocation within the broader Bittensor network.

## Introduction

Subtensor nodes play a vital role in the Bittensor network, governing various aspects such as incentivization, governance, and network health. SubVortex aims to enhance the decentralization and functionality of Bittensor by establishing an incentivised network of subtensors. This whitepaper describes the goals, roles, and operational phases of SubVortex, outlining its contribution and value proposition to the Bittensor ecosystem.

## Goals

SubVortex aspires to set the standard for subnets, prioritizing the following objectives:

- **Accessibility** - Ensuring round-the-clock availability and responsive support for miners and validators.
- **Simplicity** - Streamlining setup and updates for miners and validators, fostering ease of participation regardless of prior knowledge and technical skills.
- **Low Barrier to Entry**: Facilitating entry into Bittensor mining with minimal hardware requirements and offering fair incentives.
- **Continuous Enhancement** - Committing to ongoing improvements through a comprehensive roadmap.

## Roles

### Miner

Responsible for setting up subtensor nodes and enabling connectivity for public peers. Ownership validation of subtensors by miners is crucial for network speed, decentralization, and integrity.

### Validator

Tasked with setting up Redis instances to gather miner information, validate subtensor ownership, and compute metrics for fair rewards.

Validator has some operational phases:

- **Subtensor Phase**: Focuses on verifying miner ownership of local subtensor nodes through connectivity checks.
- **Metric Phase**: Gathers diverse metrics such as download/upload speeds, latency, and geographical data to assess miner performance.
- **Reward System**: Scores miners based on availability, latency, reliability, and global distribution, promoting network health and efficiency.

## Subtensor & Bittensor

Subtensor serves as the foundation of the Bittensor network, facilitating decentralized consensus, incentivization, staking, and governance. Its role in orchestrating the decentralized machine learning marketplace is indispensable, ensuring integrity, trust, and quality within the ecosystem.

Local Subtensor Deployment:

Running subtensors locally offers advantages in speed, reliability, and control over accessibility compared to the public Finney node. It enhances decentralization by empowering miners to manage their subtensor nodes efficiently.

## Incentive Mechanism

SubVortex's incentive mecanism will score miners based on multiple criteria of their subtensor node:

- **Availability** - Subtensor nodes must be reliable to ensure a good uptime.
- **Latency** - Subtensor nodes must be efficient to ensure a good performance.
- **Reliability** and Stability - Subtensor nodes must be efficient to ensure a good service quality.
- **Global distribution** - Subtensor nodes must be worldwide to ensure a good reach.

The final score used to set the weight is an average of all theses scoring and will replaces 5% of the weight of the previous weights.

### Availability

This reward would incentivize miners to maintain high levels of uptime and accessibility.

To assign a score for each miner, we will establish a connection with the subtensor and retrieve the current block. The score will be determined by the success of getting that block.

### Latency

This reward would incentivize miners to low-latency services and minimizing response times.

To assign a score to each miner, we will establish a connection with the subtensor and retrieve the current block. The score will be determined by the time taken to process that request, using a normalized method as part of the reward system.

The validator can be in a different country than the miner, so we will incorporate a distance-based weighting factor into the scoring formula.

### Reliability and Stability

This reward would incentivize miners to high levels of reliability and minimizing the occurrence and impact of failures.

To assign a score to each miner, we will establish a connection with the subtensor and retrieve the current block. The score will be determined by computing the ratio successes/attempts, using a normalized method as part of the reward system.

### Global Distribution

This reward would incentivize miners to effectively distribute subtensors across different geographical locations to optimize performance and reduce latency for a better subnet experience.

## Value Proposition

SubVortex enriches the Bittensor ecosystem by providing an alternative to the Finney network and promoting decentralization, reliability, and efficiency. It offers miners and validators a seamless experience with low entry barriers and continuous support.

## Team Composition

The team is compromised of individuals with diverse backgrounds and extensive experience in crypto, software development, engineering, business and data management. The SubVortex team ensures robust support and continuous improvement for the network.

Team responsabilities

- **EclipseVortex** - Development and technology
- **Ch3RNØbØG** - Operations and business development
- **tww9** - Strategy and public relations
- **HcL-CO** - QA Lead and Support

Team timezone

- **EclipseVortex** - GMT (United-Kingdom)
- **Ch3RNØbØG** - CST (USA)
- **tww9** - MST (Canada)
- **HcL-CO** - EST (Canada)

## Road Map

### Phase 1

- Create subnet in testnet and perform internal testing of the incentive mechanism
- Register subnet on mainnet
- Release preliminary information publicly

### Phase 2:

- Internal testing on mainnet. Bug fixes, etc.
- Public launch and allow key registrations.
- Basic structure with equal emissions for all miners

### Phase 3:

- Public Frontend
- Public Backend

### Phase 4

- Public SubVortex load balancer
- Performance based emission structure

> Note: The Road Map will be updated if any changes

## Conclusion

In conclusion, SubVortex stands as a cornerstone in the evolution of the Bittensor network, incentivising decentralization, reliability, and accessibility. Through its innovative approach and robust infrastructure, SubVortex aims to catalyze the growth and sustainability of the decentralized machine learning ecosystem that is Bittensor.

## Installation

### Pre-requisite

- Local Subtensor is mandatory for all miners, and highly recommended for validators.
- Validators will need to install and configure Redis

To simplify the installation process, scripts have been provided as part of this repository to ease those set up.

### Install SubVortex

Updating your base environment

```
apt update && apt upgrade -y
apt install git nodejs npm -y
npm i -g pm2
apt install python3-pip
```

Select HOME directory

```
cd $HOME
```

Clone the subnet Subvortex

```
git clone https://github.com/eclipsevortex/SubVortex.git
```

Go the the SubVortex solution

```
cd SubVortex
```

Install the dependencies

```
pip install -r requirements.txt
```

Install the base software

```
pip install -e .
```

### Install Local Subtensor

A local subtensor can be installed via docker or binary. The steps below are one of many methods. Please reference the official [Subtensor GitHub](https://github.com/opentensor/subtensor/blob/main/docs/running-subtensor-locally.md) and its [documentation](https://docs.bittensor.com/getting-started/running-a-public-subtensor#lite-node-vs-archive-node) for other ways to set up local subtensor.

Go to HOME directory

```
cd $HOME
```

Install the subtensor

```
$HOME/SubVortex/scripts/subtensor/setup.sh <NETWORK> <EXECUTION_TYPE> <ROOT_DIRECTORY>
```

Options

- `NETWORK` is the network you want you local subtensor to run against. The possible value are `localnet`, `testnet` or `mainnet`. The default value is `mainnet` and recommended to keep it as such.

- `EXECUTION_TYPE` choose `docker` if you want to install the subtensor in a docker container, `binary` to install in your base environment.

- `ROOT_DIRECTORY` is the directory where you want to install Subtensor. By default, it is set to `$HOME` and it is recommended to keep it as such.

Run the subtensor in your base environment

```
$HOME/SubVortex/scripts/subtensor/start.sh <NETWORK> <EXECUTION_TYPE> <ROOT_DIRECTORY>
```

Or via a process manager

```
pm2 start $HOME/SubVortex/scripts/subtensor/start.sh \
  --name subtensor -- \
  <NETWORK> \
  <EXECUTION_TYPE> \
  <ROOT_DIRECTORY>
```

Options

- `NETWORK` is the network you want you local subtensor to run against. The possible value are `localnet`, `testnet` or `mainnet`. The default value is `mainnet` and recommended to keep as it is.

- `EXECUTION_TYPE` choose `docker` if you want to install the subtensor in a docker container, `binary` to install in your base environment.

- `ROOT_DIRECTORY` is the directory where you want to install Subtensor. By default, it is set to `$HOME` and it is recommended to keep it as such.

You should see output like this in your pm2 logs for the process at startup:

```
> pm2 log subtensor

1|subtenso | 2023-12-22 14:21:30 🔨 Initializing Genesis block/state (state: 0x4015…9643, header-hash: 0x2f05…6c03)
1|subtenso | 2023-12-22 14:21:30 👴 Loading GRANDPA authority set from genesis on what appears to be first startup.
1|subtenso | 2023-12-22 14:21:30 🏷  Local node identity is: 12D3KooWAXnooHcMSnMpML6ooVLzFwsmt5umFhCkmkxH88LvP5gm
1|subtenso | 2023-12-22 14:21:30 💻 Operating system: linux
1|subtenso | 2023-12-22 14:21:30 💻 CPU architecture: aarch64
1|subtenso | 2023-12-22 14:21:30 💻 Target environment: gnu
1|subtenso | 2023-12-22 14:21:30 💻 Memory: 62890MB
1|subtenso | 2023-12-22 14:21:30 💻 Kernel: 5.15.0-1051-aws
1|subtenso | 2023-12-22 14:21:30 💻 Linux distribution: Ubuntu 20.04.6 LTS
1|subtenso | 2023-12-22 14:21:30 💻 Virtual machine: no
1|subtenso | 2023-12-22 14:21:30 📦 Highest known block at #0
1|subtenso | 2023-12-22 14:21:30 〽️ Prometheus exporter started at 127.0.0.1:9615
1|subtenso | 2023-12-22 14:21:30 Running JSON-RPC HTTP server: addr=0.0.0.0:9933, allowed origins=["*"]
1|subtenso | 2023-12-22 14:21:30 Running JSON-RPC WS server: addr=0.0.0.0:9944, allowed origins=["*"]
1|subtenso | 2023-12-22 14:21:31 🔍 Discovered new external address for our node: /ip4/52.56.34.197/tcp/30333/ws/p2p/12D3KooWAXnooHcMSnMpML6ooVLzFwsmt5umFhCkmkxH88LvP5gm

1|subtensor  | 2023-12-22 14:21:35 ⏩ Warping, Downloading state, 2.74 Mib (56 peers), best: #0 (0x2f05…6c03), finalized #0 (0x2f05…6c03), ⬇ 498.3kiB/s ⬆ 41.3kiB/s
1|subtensor  | 2023-12-22 14:21:40 ⏩ Warping, Downloading state, 11.25 Mib (110 peers), best: #0 (0x2f05…6c03), finalized #0 (0x2f05…6c03), ⬇ 1.1MiB/s ⬆ 37.0kiB/s
1|subtensor  | 2023-12-22 14:21:45 ⏩ Warping, Downloading state, 20.22 Mib (163 peers), best: #0 (0x2f05…6c03), finalized #0 (0x2f05…6c03), ⬇ 1.2MiB/s ⬆ 48.7kiB/s

```

### Install Redis

To install redis, refer to the [Redis guide](./scripts/redis/README.md)

### Registering your wallet

In order to run either a miner or a validator, you will need to have a wallet registered to the subnet. If you do not already have wallet set up on the server, following the steps below:

If you are restoring an existing wallet:

```
btcli w regen_coldkey --wallet.name YOUR_WALLET_NAME
btcli w regen_hotkey --wallet.name YOUR_WALLET_NAME --wallet.hotkey YOUR_HOTKEY_NAME
```

If you are creating the wallet for the first time:

```
btcli w new_coldkey --wallet.name YOUR_WALLET_NAME
btcli w new_hotkey --wallet.name YOUR_WALLET_NAME --wallet.hotkey YOUR_HOTKEY_NAME
```

Once your wallet is ready, ensure you have sufficient funds to register to the subnet. To register, use the following command:

```
btcli s register --netuid <SUBNET_UID> --subtensor.network local --wallet.name YOUR_WALLET_NAME --wallet.hotkey YOUR_HOTKEY_NAME
```

Once you have successfully registered your wallet, you are now ready to start either your miner or validator.

### Running a Miner

To run a miner, navigate to the SubVortex directory. It is highly recommended to run via a process manager like PM2.

```
pm2 start neurons/miner.py \
  --name MINER_NAME \
  --interpreter <PATH_TO_PYTHON_LIBRARY> -- \
  --netuid <SUBNET_UID> \
  --subtensor.network local \
  --wallet.name YOUR_WALLET_NAME \
  --wallet.hotkey YOUR_HOTKEY_NAME \
  --logging.debug
```

> IMPORTANT: Do not run more than one miner per machine. Running multiple miners will result in the loss of incentive and emissions on all miners.

### Running a Validator

Similar to running a miner in the above section, navigate to the SubVortex directory and run the following to launch in PM2.

```
pm2 start neurons/validator.py \
  --name VALIDATOR_NAME \
  --interpreter <PATH_TO_PYTHON_LIBRARY> -- \
  --netuid <SUBNET_UID> \
  --wallet.name YOUR_WALLET_NAME \
  --wallet.hotkey YOUR_HOTKEY_NAME \
  --logging.debug
```

> NOTE: if you run a validator in testnet do not forget to add the argument `--subtensor.network test` or `--subtensor.chain_endpoint ws://<LOCAL_SUBTENSOR_IP>:9944` (the local subtensor has to target the network testnet)

## New Releases

When a new version of the subnet is released, each miner/validatior have to be updated.

> Be sure you are in the SubVortex directory

Get the lastest version of the subnet

```
git pull
```

Install the dependencies

```
pip install -r requirements.txt
pip install -e .
```

Restart miners/validators if running them in your base environment or restart pm2 by executing `pm2 restart all` if you are using pm2 as process manager.

## Troubleshooting

### Troubleshooting Subtensor

#### State already discarded
```
Error: Service(Client(RuntimeApiError(UnknownBlock("State already discarded for 0x2f0555cc76fc2840a25a6ea3b9637146806f1f44b090c175ffde2a7e5ab36c03"))))
```

To resolve the above error, you have to purge your chain by running
```
$HOME/subtensor/target/release/node-subtensor purge-chain -y --base-path <BASE_PATH> --chain="<CHAIN>"
```

Options

`BASE_PATH` is the path used to store the state of blockahin, the default value to use is `/tmp/blockchain`.

`CHAIN` is the chain you want to use, `./raw_spec.json` for maintest and `./raw_testspec.json` for testnet.

Once the state has been purge, you can re-execute the subtensor start script $HOME/SubVortex/scripts/subtensor/start.sh via a procedd manager or not. See the section [Install Subtensor](#install-subtensor) 


## License

This repository is licensed under the MIT License.

```text
# The MIT License (MIT)
# Copyright © 2023 Yuma Rao

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
```
