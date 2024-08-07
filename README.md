<div align="center">

# **SubVortex** <!-- omit in toc -->

[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/bittensor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## An Incentivized and Decentralized Subtensor Network <!-- omit in toc -->

[Discord](https://discord.gg/bittensor) • [Network](https://taostats.io/) • [Research](https://bittensor.com/whitepaper)

---

<div>
  <img src="subvortex.png" alt="Image Description" width="310" height="200">
</div>
<br />
<div style="font-size: 20px">Testnet: 92 • Mainnet: 7</div>

</div>

---

- [Abstract](#abstract)
- [Introduction](#introduction)
- [Goals](#goals)
- [Roles](#roles)
- [Subtensor & Bittensor](#subtensor--bittensor)
- [Incentive Mechanism](#incentive-mechanism)
- [Firewall](#firewall)
- [Value Proposition](#value-proposition)
- [Team Composition](#team-composition)
- [Road Map](#road-map)
- [Credits](#credits)
- [Conclusion](#conclusion)
- [Machine Requirements](#machine-requirements)
  - [Validator](#validator-requirements)
  - [Miner](#miner-requirements)
- [Fast Setup and Run](#fast-setup-and-run)
  - [Validator](#validator-fast-setup-and-run)
  - [Miner](#miner-fast-setup-and-run)
- [Installation](#installation)
  - [Install SubVortex](#install-subvortex)
  - [Install Subtensor](#install-local-subtensor)
  - [Install Redis](#install-redis)
  - [Install Wandb](#install-wandb)
- [Registering your wallet](#registering-your-wallet)
- [Running a Miner](#running-a-miner)
- [Running a Validator](#running-a-validator)
- [Releases](#releases)
- [Troubleshooting](#troubleshooting)
  - [Troubleshooting Subtensor](#troubleshooting-subtensor)
- [License](#license)

## Abstract

SubVortex introduces an incentivized and decentralized network of subtensor nodes that are pivotal elements within the Bittensor ecosystem. This delineates the structure, objectives, and mechanisms of SubVortex, aiming to foster decentralization, stability, and efficient resource allocation within the broader Bittensor network.

## Introduction

Subtensor nodes play a vital role in the Bittensor network, governing various aspects such as incentivization, governance, and network health. SubVortex aims to enhance the decentralization and functionality of Bittensor by establishing an incentivized network of subtensors. This whitepaper describes the goals, roles, and operational phases of SubVortex, outlining its contribution and value proposition to the Bittensor ecosystem.

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

SubVortex's incentive mechanism will score miners based on multiple criteria of their subtensor node:

- **Availability** - Subtensor nodes must be reliable to ensure good uptime.
- **Latency** - Subtensor nodes must be efficient to ensure good performance.
- **Reliability** and Stability - Subtensor nodes must be efficient to ensure good service quality.
- **Global distribution** - Subtensor nodes must be worldwide to ensure a good reach.

The final score used to set the weight is an average of all these scores and will replace 5% of the weight of the previous weights.

### Availability

This reward incentivizes miners to maintain high levels of uptime and accessibility.

To assign a score for each miner, we will establish a connection with the subtensor and retrieve the current block. The score will be determined by the success of getting that block.

### Latency

This reward incentivizes miners to low-latency services and minimizes response times.

To assign a score to each miner, we will establish a connection with the subtensor and retrieve the current block. The score will be determined by the time taken to process that request, using a normalized method as part of the reward system.

The validator can be in a different country than the miner, so we will incorporate a distance-based weighting factor into the scoring formula.

### Reliability and Stability

This reward incentivizes miners to have high levels of reliability and minimize the occurrence and impact of failures.

To assign a score to each miner, we will establish a connection with the subtensor and retrieve the current block. The score will be determined by computing the ratio of successes/attempts, using a normalized method as part of the reward system.

### Global Distribution

This reward incentivizes miners to effectively distribute subtensors across different geographical locations to optimize performance and reduce latency for a better subnet experience.

## Firewall

To know more on the firewall, refer to the [firewall guide](./docs/features/firewall.md)

## Value Proposition

SubVortex enriches the Bittensor ecosystem by providing an alternative to the Finney network and promoting decentralization, reliability, and efficiency. It offers miners and validators a seamless experience with low barriers to entry and continuous support.

## Team Composition

The team comprises individuals with diverse backgrounds and extensive experience in crypto, software development, engineering, business, and data management. The SubVortex team ensures robust support and continuous improvement for the network.

Team responsabilities

- **EclipseVortex** - Development and technology
- **Ch3RNØbØG** - Operations and business development
- **CryptoMinedMind** - Strategy and public relations
- **HcL-CO** - QA Lead and support

Team timezone

- **EclipseVortex** - GMT (United-Kingdom)
- **Ch3RNØbØG** - CST (USA)
- **tww9** - MST (Canada)
- **HcL-CO** - EST (Canada)

## Road Map

### Phase 1

- Create a subnet in testnet and perform internal testing of the incentive mechanism
- Register subnet on mainnet
- Release preliminary information publicly

### Phase 2:

- Internal testing on mainnet. Bug fixes, etc.
- Public launch and allow key registrations.
- Performance-based emission structure

### Phase 3:

- Public Frontend
- Public Backend

### Phase 4

- Public SubVortex load balancer

> Note: The Road Map will be updated if there are any changes

## Credits

Bittensor technology is still new and promising, and participants are eager to support each other. That's why the SubVortex team would like to express our gratitude to everyone who has helped us reach where we are today:

- **Bittensor**: for providing a subnet template that enabled us to quickly set up our subnet.
- **Subtensor**: for their local subtensor, scripts, and invaluable assistance.
- **andrewoflaherty**: for implementing the country api using MaxMind and IPInfo ([github](https://github.com/OFlahertyAndrew))
- **Subnet Storage (SN21)**: for their excellent subnet design, which adheres to best practices and simplifies the lives of developers.
- **Users**: YES!!! Without you, we are nothing, and our vision to advance this new technology would never have materialized.
- **Others**: undoubtedly, there are many other contributors deserving of recognition, and we look forward to acknowledging them in the future.

Please don't hesitate to reach out if we've inadvertently omitted anyone, and you'd like us to give them a special shout-out on our GitHub!

## Conclusion

In conclusion, SubVortex stands as a cornerstone in the evolution of the Bittensor network, incentivizing decentralization, reliability, and accessibility. Through its innovative approach and robust infrastructure, SubVortex aims to catalyze the growth and sustainability of the decentralized machine-learning ecosystem that is Bittensor.

## Machine requirements

In terms of Operation System, you have to follow the requirements

- Ubuntu (>= 22.04)
- Others - please share with us to update our docs.

### Miner <a id="miner-requirements"></a>

For miner, you need a CPU machine (no GPU needed!) with the same requirements as a local subtensor. Go to the [Subtensor github](https://github.com/opentensor/subtensor) for more information;.

For more information, take a look on the [min requirements](./min_compute.yml)

> IMPORTANT: take a look at the [Incentive Mechanism](#incentive-mechanism) to understand better where you can play to get the best miner. To summarize, you need to be available, reliable, and present in various geographical locations with low latency.

### Validator <a id="validator-requirements"></a>

For validator, you need a CPU machine (no GPU needed!).

For more information, take a look on the [min requirements](./min_compute.yml)

## Fast Setup and Run

For a quick and seamless setup, we provide a comprehensive script that installs and runs a miner or validator, taking care of everything from installation to execution.

### Setup and run a miner <a id="miner-fast-setup-and-run"></a>

> **IMPORTANT** <br />
> To use the full script, you have to follow the steps to install the subnet (**EXCEPT** executing **subnet_setup.sh**) by following the [Subnet guide](./scripts/subnet/README.md)

Be sure you are in the **SubVortex** directory, if not

```
cd SubVortex
```

Then, you can run the script

```
./scripts/setup_and_run.sh -t miner
```

> IMPORTANT
>
> - If you any prompts, just confirm them
> - Other options are available, pleaser take a look

Check the available options by running

```
./scripts/setup_and_run.sh -h
```

Once the script is successfully executed, you'll have a miner up and running—nothing else required!

Of course, if you have specific settings in mind, you can use this script as a base and update anything you want to tailor your experience to your needs.

Finally, if you prefer setup and run the miner in a more controlled way, you can follow the different sections below.

### Setup and run a validator <a id="validator-fast-setup-and-run"></a>

> **IMPORTANT** <br />
> To use the full script, you have to follow the steps to install the subnet (**EXCEPT** executing **subnet_setup.sh**) by following the [Subnet guide](./scripts/subnet/README.md)

Be sure you are in the **SubVortex** directory, if not

```
cd SubVortex
```

Then, you can run the script

```
./scripts/setup_and_run.sh -t validator
```

Check the available options by running

```
./scripts/setup_and_run.sh -h
```

Once the script is successfully executed, you'll have a validator up and running—nothing else required!

Of course, if you have specific settings in mind, you can use this script as a base and update anything you want to tailor your experience to your needs.

Finally, if you prefer setup and run the validator in a more controlled way, you can follow the different sections below.

## Installation

### Pre-requisite

- Local Subtensor is mandatory for all miners, and highly recommended for validators.
- Validators will need to install and configure Redis

### Install SubVortex

To install the subnet, refer to the [Subnet guide](./scripts/subnet/README.md)

### Install Local Subtensor

To install a local subtensor, refer to the [Subtensor guide](./scripts/subtensor/README.md)

### Install Redis

To install redis, refer to the [Redis guide](./scripts/redis/README.md)

### Install Wandb

To install wandb, refer to the [Wandb guide](./docs/wandb/wandb.md)

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

> IMPORTANT: Before running a miner, be sure you have a local subtensor up and running. Please see the [Subtensor guide](./scripts/subtensor/README.md) for more details.

> IMPORTANT: **wandb** **IS NOT** for miners, **ONLY FOR** validators.

To run a miner, navigate to the SubVortex directory. It is highly recommended to run via a process manager like PM2.

```
pm2 start neurons/miner.py \
  --name MINER_NAME \
  --interpreter <PATH_TO_PYTHON_LIBRARY> -- \
  --netuid <SUBNET_UID> \
  --wallet.name YOUR_WALLET_NAME \
  --wallet.hotkey YOUR_HOTKEY_NAME \
  --subtensor.network local \
  --logging.debug \
  --auto-update
```

> IMPORTANT: Do not run more than one miner per machine. Running multiple miners will result in the loss of incentive and emissions on all miners.

To enable the firewall, add the `--firewall.on` flag. It is highly recommended to enable the firewall to protect your miner from attacks that could impact your score. For more details about the firewall, please refer to our [firewall guide](./docs/features/firewall.md)

### Running a Validator

> IMPORTANT: Before running a validator, be sure you have a redis up and running. Please see the [Redis guide](./scripts/redis/README.md) for more details.

> IMPORTANT: Before running a validator, be sure you have a local subtensor up and running. Please see the [Subtensor guide](./scripts/subtensor/README.md) for more details.

> IMPORTANT: By default wandb is enabled when running a validator. It is **HIGHLY RECOMMANDED** to not disable it as it enables everyone to access various statistics for better performance on the subnet but if you want to do it, just add `--wandb.off` to the followed pm2 command. If you want to keep wandb enabled, please refer to the [Wandb guide](./docs/wandb/wandb.md) for more details as there are some manually steps to go throught before running the validator.

> Please use `--database.index <INDEX>`if you have multiple subnet sharing the same redis instance and the index 1 (default value) is already taken by another subnet

Similar to running a miner in the above section, navigate to the SubVortex directory and run the following to launch in PM2.

```
pm2 start neurons/validator.py \
  --name VALIDATOR_NAME \
  --interpreter <PATH_TO_PYTHON_LIBRARY> -- \
  --netuid <SUBNET_UID> \
  --wallet.name YOUR_WALLET_NAME \
  --wallet.hotkey YOUR_HOTKEY_NAME \
  --subtensor.network local \
  --logging.debug \
  --auto-update
```

> NOTE: if you run a validator in testnet do not forget to add the argument `--subtensor.network test` or `--subtensor.chain_endpoint ws://<LOCAL_SUBTENSOR_IP>:9944` (the local subtensor has to target the network testnet)

> NOTE: to access the wandb UI to get statistics about the miners, you can click on this [link](https://wandb.ai/eclipsevortext/subvortex-team) and choose the validator run you want.

> NOTE: by default the dumps created by the auto-update will be stored in /etc/redis. If you want to change the location, please use `--database.redis_dump_path`.

## Releases

- [Release-2.2.0](./scripts/release/release-2.2.0/RELEASE-2.2.0.md)

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
# Copyright © 2024 Eclipse Vortex

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
