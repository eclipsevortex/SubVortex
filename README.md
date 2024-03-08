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
<div>Testnet: 92 • Mainnet: TBD</div>

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
- [Installation](#installation-links)
  - [Install SubVortex](#install-subvortex)
  - [Install Miner](#install-miner)
  - [Install Validator](#install-validator)
  - [Install Subtensor](#install-subtensor)
  - [Install Redis](#install-redis)
- [New Releases](#new-releases)
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
- **HcL-CO** - Technical support

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

### Before you proceed

Before you proceed with the installation of the subnet, note the following:

- Use these instructions to run your subnet locally for your development and testing, or on Bittensor testnet or on Bittensor mainnet.
- **IMPORTANT**: We **strongly recommend** that you first run your subnet locally and complete your development and testing before running the subnet on Bittensor testnet. Furthermore, make sure that you next run your subnet on Bittensor testnet before running it on the Bittensor mainnet.
- You can run your subnet either as a subnet owner, or as a subnet validator or as a subnet miner.
- **IMPORTANT:** Make sure you are aware of the minimum compute requirements for your subnet. See the [Minimum compute YAML configuration](./min_compute.yml).
- Note that installation instructions differ based on your situation: For example, installing for local development and testing will require a few additional steps compared to installing for testnet. Similarly, installation instructions differ for a subnet owner vs a validator or a miner.

### Install SubVortex

In order to run miner, validator or use some scripts that make your experience easier, you have to install the subnet SubVortex by following the steps.

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

### Install Miner

As pre-requisite, a local subtensor have to be up and running on the machine the miner will be installed. For the instruction to install a local subtensor, refer to the section [Install Subnet](#install-subnet)

Then, install the subnet SubVortex (if not already done) by following the instructions in the section [Install SubVortex](#install-subvortex)

Finally, run the miner

> Be sure you are in the SubVortex directory

> NOTE: When registering a miner, it is highly recommended to not reuse hotkeys. Best practice is to always use a new hotkey when registering on the subnet.

You can run the miner in your base environment

```
python3 neurons/miner.py \
  --netuid <SUBNET_UID> \
  --subtensor.network local \
  --wallet.name <COLDKEY_NAME> \
  --wallet.hotkey <HOTKEY_NAME> \
  --logging.debug
```

But it is highly recommanded to run it via a process manager

```
pm2 start neurons/miner.py \
  --name <UNIQUE_NAME> \
  --interpreter <PATH_TO_PYTHON_LIBRARY> -- \
  --netuid <SUBNET_UID> \
  --subtensor.network local \
  --wallet.name <COLDKEY_NAME> \
  --wallet.hotkey <HOTKEY_NAME> \
  --logging.debug
```

> Do not change the argument `--subtensor.network` as you have to use the local subtensor running on the same machine as the miner.

Options

`--netuid`: Specifies the chain subnet uid. Default: 21.

`--miner.name`: Name of the miner, used for organizing logs and data. Default: "core_storage_miner".

`--miner.device`: Device to run the miner on, e.g., "cuda" for GPUs or "cpu" for CPU. Default depends on CUDA availability.

`--miner.verbose`: Enables verbose logging. Default: False.

`--miner.mock_subtensor`: If True, uses a mock subtensor for testing. Default: False.

These options allow you to configure the miner's behavior, database connections, blacklist/whitelist settings, priority handling, and integration with monitoring tools like WandB. Adjust these settings based on your mining setup and requirements.

### Install Validator

As pre-requisite, a redis instance have to be up and running on the machine the validator will be installed. For the instruction to install a redis instance, refer to the section [Install Redis](#install-redis)

Then, install the subnet SubVortex (if not already done) by following the instructions in the section [Install SubVortex](#install-subvortex)

Finally, run the validator

> Be sure you are in the SubVortex directory

> NOTE: When registering a validator, it is highly recommended to not reuse hotkeys. Best practice is to always use a new hotkey when registering on the subnet.

You can run the validator in your base environment

```
python3 neurons/validator.py \
  --netuid <SUBNET_UID> \
  --wallet.name <COLDKEY_NAME> \
  --wallet.hotkey <HOTKEY_NAME> \
  --logging.debug
```

But it is highly recommanded to run it via a process manager

```
pm2 start neurons/validator.py \
  --name <UNIQUE_NAME> \
  --interpreter <PATH_TO_PYTHON_LIBRARY> -- \
  --netuid <SUBNET_UID> \
  --wallet.name <COLDKEY_NAME> \
  --wallet.hotkey <HOTKEY_NAME> \
  --logging.debug
```

> It is highly recommended that all miners and validators to run their own local subtensor node. This will resolve the many issues commonly found with intermittent connectivity across all subnets. To do that, use the argument `--subtensor.chain_endpoint ws://<SUBTENSOR_IP>:9944`

Options
`--neuron.name`: Specifies the name of the validator neuron. Default: "core_storage_validator".

`--neuron.device`: The device to run the validator on (e.g., "cuda" for GPU, "cpu" for CPU). Default: "cuda" if CUDA is available, else "cpu".

`--neuron.curve`: The elliptic curve used for cryptography. Only "P-256" is currently available.

`--neuron.maxsize`: The maximum size of random data to store. If None, a lognormal random Gaussian distribution is used (default: None).

`--neuron.disable_log_rewards`: If set, disables all reward logging to suppress function values from being logged (e.g., to WandB). Default: False.

`--neuron.num_concurrent_forwards`: The number of concurrent forward requests running at any time. Default: 1.

`--neuron.disable_set_weights`: If set, disables setting weights on the chain. Default: False.

`--neuron.checkpoint_block_length`: Blocks before a checkpoint is saved. Default: 100.

`--neuron.events_retention_size`: File size for retaining event logs (e.g., "2 GB"). Default: "2 GB".

`--neuron.dont_save_events`: If set, event logs will not be saved to a file. Default: False.

`--neuron.vpermit_tao_limit`: The maximum TAO allowed for querying a validator with a vpermit. Default: 500.

`--neuron.verbose`: If set, detailed verbose logs will be printed. Default: False.

`--neuron.log_responses`: If set, all responses will be logged. Note: These logs can be extensive. Default: False.

`--neuron.data_ttl`: The number of blocks before stored challenge data expires. Default: 50000 (approximately 7 days).

`--neuron.profile`: If set, network and I/O actions will be profiled. Default: False.

`--database.host`: Hostname of the Redis database. Default: "localhost".

`--database.port`: Port of the Redis database. Default: 6379.

`--database.index`: The database number for the Redis instance. Default: 1.

These options allow you to fine-tune the behavior, storage, and network interaction of the validator neuron. Adjust these settings based on your specific requirements and infrastructure.

### Install Subtensor

A local subtensor can be installed via docker or binary. The instructions can be found on the official github repository [subtensor](https://github.com/opentensor/subtensor/blob/main/docs/running-subtensor-locally.md) with the help of the offical [documentation](https://docs.bittensor.com/getting-started/running-a-public-subtensor#lite-node-vs-archive-node)

You should see output like this in your pm2 logs for the process at startup:

```
> pm2 logs subtensor

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

> Be sure you are in the SubVortex directory

Install redis

```
./scripts/redis/install_redis.sh
```

Set Redis password

```
./scripts/redis/set_redis_password.sh
```

Create Redis firewall

```
./scripts/redis/create_redis_firewall.sh
```

Disable Rdb

```
./scripts/redis/disable_rdb.sh
```

Check redis is up and running

```
./scripts/redis/test_persistence.sh
```

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
```

Restart miners/validators if running them in your base environment or restart pm2 by executing `pm2 restart all` if you are using pm2 as process manager.

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
