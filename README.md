<div align="center">

# **SubVortex** <!-- omit in toc -->

[![Build & Push](https://github.com/eclipsevortex/SubVortex/actions/workflows/docker-workflow.yml/badge.svg)](https://github.com/eclipsevortex/SubVortex/actions/workflows/docker-workflow.yml)
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
- [Subtensor & Bittensor](#subtensor-and-bittensor)
- [Incentive Mechanism](#incentive-mechanism)
- [Firewall](#firewall)
- [Value Proposition](#value-proposition)
- [Leadership & Operations](#leardership-and-operations)
- [Credits](#credits)
- [Conclusion](#conclusion)
- [Machine Requirements](#machine-requirements)
  - [Validator](#validator-requirements)
  - [Miner](#miner-requirements)
- [Registering your wallet](#registering-your-wallet)
- [Quick Setup](#quick-setup)
  - [Miner](#quick-setup-miner)
  - [Validator](#quick-setup-validator)
- [Neuron Management](#neuron-management)
  - [Miner](#miner-management)
  - [Validator](#validator-management)
- [Installation](#installation)
  - [Install Subtensor](#install-local-subtensor)
  - [Install Wandb](#install-wandb)
- [Troubleshooting](#troubleshooting)
  - [Troubleshooting Subtensor](#troubleshooting-subtensor)
- [License](#license)

<br />

## 📄 Abstract <a id="abstract"></a>

SubVortex introduces an incentivized and decentralized network of subtensor nodes that are pivotal elements within the Bittensor ecosystem. This delineates the structure, objectives, and mechanisms of SubVortex, aiming to foster decentralization, stability, and efficient resource allocation within the broader Bittensor network.

## 👋 Introduction <a id="introduction"></a>

Subtensor nodes play a vital role in the Bittensor network, governing various aspects such as incentivization, governance, and network health. SubVortex aims to enhance the decentralization and functionality of Bittensor by establishing an incentivized network of subtensors. This whitepaper describes the goals, roles, and operational phases of SubVortex, outlining its contribution and value proposition to the Bittensor ecosystem.

## 🎯 Goals <a id="goals"></a>

SubVortex aspires to set the standard for subnets, prioritizing the following objectives:

- **Accessibility** - Ensuring round-the-clock availability and responsive support for miners and validators.
- **Simplicity** - Streamlining setup and updates for miners and validators, fostering ease of participation regardless of prior knowledge and technical skills.
- **Low Barrier to Entry**: Facilitating entry into Bittensor mining with minimal hardware requirements and offering fair incentives.
- **Continuous Enhancement** - Committing to ongoing improvements through a comprehensive roadmap.

## 🧑‍💻 Roles <a id="roles"></a>

### Miner

Responsible for setting up subtensor nodes and enabling connectivity for public peers. Ownership validation of subtensors by miners is crucial for network speed, decentralization, and integrity.

### Validator

Tasked with setting up Redis instances to gather miner information, validate subtensor ownership, and compute metrics for fair rewards.

Validator has some operational phases:

- **Subtensor Phase**: Focuses on verifying miner ownership of local subtensor nodes through connectivity checks.
- **Metric Phase**: Gathers diverse metrics such as download/upload speeds, latency, and geographical data to assess miner performance.
- **Reward System**: Scores miners based on availability, latency, reliability, and global distribution, promoting network health and efficiency.

## 🧠 Subtensor & Bittensor <a id="subtensor-and-bittensor"></a>

Subtensor serves as the foundation of the Bittensor network, facilitating decentralized consensus, incentivization, staking, and governance. Its role in orchestrating the decentralized machine learning marketplace is indispensable, ensuring integrity, trust, and quality within the ecosystem.

Local Subtensor Deployment:

Running subtensors locally offers advantages in speed, reliability, and control over accessibility compared to the public Finney node. It enhances decentralization by empowering miners to manage their subtensor nodes efficiently.

## 💰 Incentive Mechanism <a id="incentive-mechanism"></a>

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

## 🛡️ Firewall <a id="firewall"></a>

To know more on the firewall, refer to the [firewall guide](./docs/features/firewall.md)

## 🏆 Value Proposition <a id="value-proposition"></a>

SubVortex enriches the Bittensor ecosystem by providing an alternative to the Finney network and promoting decentralization, reliability, and efficiency. It offers miners and validators a seamless experience with low barriers to entry and continuous support.

## 👤 Leadership & Operations <a id="leardership-and-operations"></a>

SubVortex is driven by a highly focused and performance-oriented team with deep experience in crypto, software engineering, infrastructure, and data systems. With a commitment to transparency and continuous improvement, the team ensures robust support for validators, miners, and the broader Bittensor ecosystem.

We are constantly evolving and expanding, and contributors from the community are welcome as we scale.

Core responsabilities

- **EclipseVortex** - Architecture, infrastructure, and development leadership

Operational Timezone

- **EclipseVortex** - GMT (United-Kingdom)

## 🙌 Credits <a id="credits"></a>

Bittensor technology is still new and promising, and participants are eager to support each other. That's why the SubVortex team would like to express our gratitude to everyone who has helped us reach where we are today:

- **Bittensor**: for providing a subnet template that enabled us to quickly set up our subnet.
- **Subtensor**: for their local subtensor, scripts, and invaluable assistance.
- **andrewoflaherty**: for implementing the country api using MaxMind and IPInfo ([github](https://github.com/OFlahertyAndrew))
- **Subnet Storage (SN21)**: for their excellent subnet design, which adheres to best practices and simplifies the lives of developers.
- **Users**: YES!!! Without you, we are nothing, and our vision to advance this new technology would never have materialized.
- **Others**: undoubtedly, there are many other contributors deserving of recognition, and we look forward to acknowledging them in the future.

Please don't hesitate to reach out if we've inadvertently omitted anyone, and you'd like us to give them a special shout-out on our GitHub!

## 🔚 Conclusion <a id="conclusion"></a>

In conclusion, SubVortex stands as a cornerstone in the evolution of the Bittensor network, incentivizing decentralization, reliability, and accessibility. Through its innovative approach and robust infrastructure, SubVortex aims to catalyze the growth and sustainability of the decentralized machine-learning ecosystem that is Bittensor.

## 🖥️ Machine requirements <a id="machine-requirements"></a>

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

## 🦊 Registering your wallet <a id="registering-your-wallet"></a>

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

## 🚀 Quick Setup <a id="quick-setup"></a>

⚠️ **Recommended Setup Method — Use the Auto Upgrader**

To safely and efficiently install and manage your SubVortex miner or validator, we strongly recommend using the [SubVortex Auto Upgrader](https://github.com/eclipsevortex/SubVortex.AutoUpgrader).
This tool handles:

- Initial installation
- Service restarts
- Zero-downtime upgrades
- Version tracking and rollback
- Safe Redis and file migrations

❗ If you proceed with the manual `Quick Setup` scripts below, you do so at your own risk. You’ll be responsible for future upgrades, downtime handling, and configuration issues.

➡️ For long-term reliability and simplicity, use the Auto Upgrader.

<br />

Before running a validator and/or a miner, you have to

1. Create or recreate your wallets (coldkey + hotkey) - [more details](#registering-your-wallet)
2. Register to the subnet - [more details](#registering-your-wallet)
3. Copy the template to .env in the same directory and update the values for your specific setup.

Each `.env` file maps directly to the arguments used by the service. Use the format `SUBVORTEX_<ARG>` based on the command-line flag. For example, `--database.password` becomes `SUBVORTEX_DATABASE_PASSWORD`.

There’s one `env.template` per service (e.g. miner/neuron/env.template, validator/redis/env.template, etc.), so make sure to configure each role accordingly.

### Miner <a id="quick-setup-miner"></a>

To start the SubVortex miner in a quick way, you can run

```bash
./subvortex/miner/scripts/quick_start.sh
```

It will install and start the miner as service which is the default mode.

Use `-h` to see the options

To stop the SubVortex miner in a quick way, you can run

```bash
./subvortex/miner/scripts/quick_stop.sh
```

It will stop and teardown the miner as service which is the default mode.

Use `-h` to see the options

### Validator <a id="quick-setup-validator"></a>

To start the SubVortex validator in a quick way, you can run

```bash
./subvortex/validator/scripts/quick_start.sh
```

It will install and start the validator as service which is the default mode.

Use `-h` to see the options

To stop the SubVortex validator in a quick way, you can run

```bash
./subvortex/validator/scripts/quick_stop.sh
```

It will stop and teardown the validator as service which is the default mode.

Use `-h` to see the options

## ⚙️ Neuron Management <a id="neuron-management"></a>

⚠️ **Manual Service Management — Use with Caution**

While SubVortex provides CLI scripts to manage miners and validators manually, this approach is intended only for advanced users or for debugging purposes.
For production environments, please use the SubVortex Auto Upgrader to:
- Automatically handle upgrades, rollbacks, and migrations
- Keep services up-to-date and running reliably
- Minimize risk of misconfiguration or downtime

❗ Managing neuron services manually means you are fully responsible for infrastructure stability, update coordination, and service integrity.

➡️ Unless you have a strong reason, we highly recommend switching to the Auto Upgrader.

This section explains the different action you can execute on a miner and/or validator.

### Miner <a id="miner-management"></a>

A **miner** is made up of one or more services located in the `subvortex/miner` directory.

Each service includes a `scripts/` folder, which provides a simple interface to control the service with the following actions:

- `setup` – Prepare the service environment
- `start` – Launch the service
- `stop` – Stop the service
- `teardown` – Clean up everything related to the service

To stop the miner neuron service, run:

```bash
./subvortex/miner/neuron/scripts/neuron_stop.sh
```

Need help? You can pass `-h` to any of these scripts to view the available options:

```bash
./subvortex/miner/neuron/scripts/neuron_stop.sh -h
```

These scripts are wrappers around lower-level implementations found in the `deployment/` directory. This directory is organized by **execution type**:

- `service`
- `process`
- `docker` (soon to be renamed to `container`)

Each of these directories contains specialized logic for running the services in different environments or configurations.

You **don’t need to worry about these inner workings**. The top-level `scripts/` handle it for you. When needed, just pass the `--execution` flag to specify which mode to use, like so:

```bash
./subvortex/miner/neuron/scripts/neuron_start.sh --execution process
```

This keeps your interaction simple, while giving you full control when you need it.

### Validator <a id="validator-management"></a>

A **validator** is made up of one or more services located in the `subvortex/validator` directory.

Each service includes a `scripts/` folder, which provides a simple interface to control the service with the following actions:

- `setup` – Prepare the service environment
- `start` – Launch the service
- `stop` – Stop the service
- `teardown` – Clean up everything related to the service

To stop the miner neuron service, run:

```bash
./subvortex/validator/neuron/scripts/neuron_stop.sh
```

Need help? You can pass `-h` to any of these scripts to view the available options:

```bash
./subvortex/validator/neuron/scripts/neuron_stop.sh -h
```

These scripts are wrappers around lower-level implementations found in the `deployment/` directory. This directory is organized by **execution type**:

- `service`
- `process`
- `docker` (soon to be renamed to `container`)

Each of these directories contains specialized logic for running the services in different environments or configurations.

You **don’t need to worry about these inner workings**. The top-level `scripts/` handle it for you. When needed, just pass the `--execution` flag to specify which mode to use, like so:

```bash
./subvortex/validator/neuron/scripts/neuron_start.sh --execution process
```

This keeps your interaction simple, while giving you full control when you need it.

## 🛠️ Installation <a id="installation"></a>

### Pre-requisite

- Local Subtensor is mandatory for all miners, and highly recommended for validators.
- Validators will need to install and configure Redis

### Install Local Subtensor

To install a local subtensor, refer to the [Subtensor guide](./scripts/subtensor/README.md)

### Install Wandb

To install wandb, refer to the [Wandb guide](./docs/wandb/wandb.md)

## 🔧 Troubleshooting <a id="troubleshooting"></a>

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

## 🪪 License <a id="license"></a>

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
