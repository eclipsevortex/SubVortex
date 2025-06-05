# SubVortex Validator Guide

This document provides a comprehensive guide on how to set up and run the SubVortex Validator. The SubVortex Validator is used to ensure its role of nodes manager in the context of SubVortex.

<br />

---

- [Installation](#installation)
  - [As process](#installation-as-process)
  - [As service](#installation-as-service)
  - [As docker container](#installation-as-container)
- [Uninstall](#uninstall)
  - [As process](#uninstall-as-process)
  - [As service](#uninstall-as-service)
  - [As docker container](#uninstall-as-container)
- [Querier](#querier)

---

<br />

> ⚠️ **Architecture Notice**  
> The Validator currently supports only **x86_64 (amd64)** servers.  
> `arm64` support is not yet available but is a work in progress.

<br />

# Installation

Before getting started, you need to create an .env file with the correct configuration. To generate it, run

```
cp .env.template .env
```

Then, open `.env` in a text editor and update it with your settings.

## As process <a id="installation-as-process"></a>

> **IMPORTANT** <br />
> Before starting, be sure pm2 is installed if you decide to run the Validator in a process, see [pm2 installation](../../../scripts/process/README.md)

To setup the Validator, you can run

```bash
./subvortex/validator/neuron/deployment/process/neuron_process_setup.sh
```

To start the Validator, you can run

```bash
./subvortex/validator/neuron/deployment/process/neuron_process_start.sh
```

To check the Validator is up and running, you can run

```bash
pm2 log subvortex-validator-neuron
```

You should see something like

```bash
2025-05-02 11:51:43.474 |      DEBUG       | validator version 3.0.0
2025-05-02 11:51:43.474 |      DEBUG       | loading wallet
2025-05-02 11:51:43.475 |      DEBUG       | loading subtensor
2025-05-02 11:51:43.475 |      DEBUG       | Connecting to network: finney, chain_endpoint: wss://entrypoint-finney.opentensor.ai:443> ...
2025-05-02 11:51:45.444 |      DEBUG       | Network: finney, Chain: wss://entrypoint-finney.opentensor.ai:443
2025-05-02 11:51:45.501 |      DEBUG       | wallet: Wallet (Name: 'subvortex', Hotkey: 'default', Path: '~/.bittensor/wallets/')
2025-05-02 11:51:45.502 |      DEBUG       | loading metagraph
2025-05-02 11:51:46.356 |      DEBUG       | metagraph(netuid:7, n:256, block:4444028, network:finney)
```

## As service <a id="installation-as-service"></a>

> ⚠️ **Manual Installation**  
> If you are not using the **Auto Upgrader**, do not forget to add `SUBVORTEX_USE_LOCAL_WORKDIR=True` in your `.env`.

To setup the Validator, you can run

```bash
./subvortex/validator/neuron/deployment/service/neuron_service_setup.sh
```

To start the Validator, you can run

```bash
./subvortex/validator/neuron/deployment/service/neuron_service_start.sh
```

To check the Validator is up and running, you can run

```bash
systemctl status subvortex-validator-neuron
```

You should see something like

```bash
 subvortex-validator-neuron.service - SubVortex Validator Neuron
     Loaded: loaded (/etc/systemd/system/subvortex-validator-neuron.service; disabled; vendor preset: enabled)
     Active: active (running) since Mon 2025-05-05 17:42:06 BST; 8s ago
   Main PID: 775722 (python3)
      Tasks: 18 (limit: 28765)
     Memory: 163.7M
        CPU: 4.837s
     CGroup: /system.slice/subvortex-validator-neuron.service
             └─775722 /root/subvortex/subvortex/validator/neuron/venv/bin/python3 -m subvortex.validator.neuron.src.main --subtensor.network test --floatting.flag stable --wallet.hotkey default --database.host localhost --axon.>

May 05 17:42:06 vmi1610615.contaboserver.net systemd[1]: Started SubVortex Validator Neuron.
```

## As docker container <a id="installation-as-container"></a>

> **IMPORTANT** <br />
> Before starting, be sure docker is installed if you decide to run the Validator as docker container, see [docker installation](../../../scripts/docker/README.md)

If you are not using the Auto Upgrader, you have to prefix all these commands by

```bash
export SUBVORTEX_FLOATTING_FLAG=latest
```

For testnet, you can use `latest` (release) or `stable` (release candidate).

To build the Validator, you can run

```bash
./subvortex/validator/neuron/deployment/docker/neuron_docker_setup.sh
```

To start the Validator, you can run

```bash
./subvortex/validator/neuron/deployment/docker/neuron_docker_start.sh
```

To check the Validator is up and running, you can run

```bash
docker ps
```

You should see a container named `subvortex-validator-neuron`.

You can even check the logs, by running

```bash
docker logs subvortex-validator-neuron`
```

You should see something like

```bash
2025-05-02 11:51:43.474 |      DEBUG       | validator version 3.0.0
2025-05-02 11:51:43.474 |      DEBUG       | loading wallet
2025-05-02 11:51:43.475 |      DEBUG       | loading subtensor
2025-05-02 11:51:43.475 |      DEBUG       | Connecting to network: finney, chain_endpoint: wss://entrypoint-finney.opentensor.ai:443> ...
2025-05-02 11:51:45.444 |      DEBUG       | Network: finney, Chain: wss://entrypoint-finney.opentensor.ai:443
2025-05-02 11:51:45.501 |      DEBUG       | wallet: Wallet (Name: 'subvortex', Hotkey: 'default', Path: '~/.bittensor/wallets/')
2025-05-02 11:51:45.502 |      DEBUG       | loading metagraph
2025-05-02 11:51:46.356 |      DEBUG       | metagraph(netuid:7, n:256, block:4444028, network:finney)
```

<br />

# Uninstall

## As process <a id="uninstall-as-process"></a>

To uninstall the Validator, you can run

```bash
./subvortex/validator/neuron/deployment/process/neuron_process_teardown.sh
```

To check the Validator has been uninstalled, you can run

```bash
pm2 list
```

You should not see any process named `subvortex-validator-neuron`.

## As service <a id="uninstall-as-service"></a>

To uninstall the Validator, you can run

```bash
./subvortex/validator/neuron/deployment/service/neuron_service_teardown.sh
```

To check the Validator has been uninstalled, you can run

```bash
systemctl status subvortex-validator-neuron
```

You should see something like

```bash
Unit subvortex-validator-neuron.service could not be found.
```

## As docker container <a id="uninstall-as-container"></a>

If you are not using the Auto Upgrader, you have to prefix all these commands by

```bash
export SUBVORTEX_FLOATTING_FLAG=latest
```

To uninstall the Validator, you can run

```bash
./subvortex/validator/neuron/deployment/docker/neuron_docker_teardown.sh
```

To check the Validator has been uninstalled, you can run

```bash
docker ps
```

You should not see any container named `subvortex-validator-neuron`.

<br />

# Querier

The **Querier** is a CLI tool to inspect and analyze the current state of Redis-synced neurons or miners. It supports filters, sorting, column selection, and pagination to help navigate large datasets efficiently.

To run the Querier, use:

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh --namespace=<neuron|miner> [options]
```

---

### ✅ Basic Usage

Query all neurons:

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh --namespace=neuron
```

Query all miners:

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh --namespace=miner
```

---

### 🎯 Filtering Data

You can filter neurons or scores using various operators:

| Operator    | Example                                  | Description                           |
| ----------- | ---------------------------------------- | ------------------------------------- |
| `=` or `==` | `--filter uid=42`                        | Equals                                |
| `!=`        | `--filter hotkey!=abcd`                  | Not equals                            |
| `>` / `<`   | `--filter stake>100`                     | Greater or less than (numeric only)   |
| `>=` / `<=` | `--filter trust>=0.5`                    | Greater or equal / less or equal      |
| `in`        | `--filter "country in FR,DE,US"`         | Field is one of the listed values     |
| `not in`    | `--filter "ip not in 0.0.0.0,127.0.0.1"` | Field is not one of the listed values |

You can use `--filter` multiple times to apply multiple conditions.

---

### 🧾 Selecting Fields

By default, Querier displays all available fields that fit in your terminal. To manually select which fields to show:

```bash
--fields=uid,ip,country,stake
```

Example:

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh --namespace=neuron --fields=uid,stake,hotkey
```

---

### 📊 Sorting

Sort results by any numeric or string field. Use a minus `-` prefix to sort in descending order:

```bash
--sort=stake        # Ascending
--sort=-stake       # Descending
```

Example:

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh  --namespace=neuron --sort=-uid
```

---

### 📃 Pagination

The Querier paginates results by default. To customize the number of rows per page:

```bash
--page-size=50
```

Press `Enter` to continue to the next page.

---

### 🛠️ Common Use Cases

#### Show my neuron

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh \
  --namespace=neuron \
  --filter uid=60
```

#### Show all neurons from a country or multiple country

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh \
  --namespace=neuron \
  --filter country=FR \
  --fields uid,hotkey,registered_at,ip,is_serving,version
```

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh \
  --namespace=neuron \
  --filter "country in FR,ES" \
  --fields uid,hotkey,registered_at,ip,is_serving,version
```

#### Show top 10 miners

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh \
  --namespace=neuron \
  --sort=-rank \
  --page-size 10 \
  --fields uid,hotkey,country,incentive
```

#### Show validators

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh \
  --namespace=neuron \
  --sort=-dividends \
  --page-size 10 \
  --fields uid,hotkey,country,dividends \
  --filter "validator_trust>0" \
  --filter "stake>1000"
```

#### Show miner's scores

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh \
  --namespace=miner \
  --filter uid=60 \
  --fields uid,hotkey,moving_score,score,availability_score,reliability_score,latency_score,distribution_score
```

#### Show top 10 miners

```bash
./subvortex/validator/neuron/scripts/neuron_querier.sh \
  --namespace=miner \
  --sort=-moving_score \
  --page-size 10 \
  --fields uid,hotkey,moving_score,score,availability_score,reliability_score,latency_score,distribution_score
```