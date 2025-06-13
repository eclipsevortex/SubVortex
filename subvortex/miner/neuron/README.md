# SubVortex Miner Guide

This document provides a comprehensive guide on how to set up and run the SubVortex Miner. The SubVortex miner is used to ensure its role of nodes manager in the context of SubVortex.

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
> The Miner currently supports only **x86_64 (amd64)** servers.  
> `arm64` support is not yet available but is a work in progress.

<br />

# Installation

Before getting started, you need to create an .env file with the correct configuration. To generate it, run

```bash
cp .env.template .env
```

Then, open `.env` in a text editor and update it with your settings.

## As process <a id="installation-as-process"></a>

> **IMPORTANT** <br />
> Before starting, be sure pm2 is installed if you decide to run the Miner in a process, see [pm2 installation](../../../scripts/process/README.md)

To setup the Miner, you can run

```bash
./subvortex/miner/neuron/deployment/process/neuron_process_setup.sh
```

To start the Miner, you can run

```bash
./subvortex/miner/neuron/deployment/process/neuron_process_start.sh
```

To check the SubVortex Miner is up and running, you can run

```bash
pm2 log subvortex-miner-neuron
```

You should see something like

```bash
2025-05-02 11:55:28.402 |      DEBUG       | miner version 3.0.0
2025-05-02 11:55:28.404 |      DEBUG       | [File Monitoring] started
ColdKey for the wallet 'miner' already exists.
HotKey for the wallet 'miner' already exists.
2025-05-02 11:55:28.427 |      DEBUG       | loading wallet
2025-05-02 11:55:28.434 |      DEBUG       | wallet: Wallet (Name: 'miner', Hotkey: 'default', Path: '~/.bittensor/wallets/')
2025-05-02 11:55:28.434 |      DEBUG       | loading subtensor
2025-05-02 11:55:28.435 |      DEBUG       | Connecting to network: local, chain_endpoint: ws://127.0.0.1:9944> ...
2025-05-02 11:55:30.091 |      DEBUG       | Network: local, Chain: ws://127.0.0.1:9944
2025-05-02 11:55:30.093 |      DEBUG       | checking wallet registration
2025-05-02 11:55:30.105 |      DEBUG       | loading metagraph
2025-05-02 11:55:30.607 |      DEBUG       | metagraph(netuid:7, n:256, block:4444047, network:finney)
2025-05-02 11:55:30.609 |       INFO       | Running miner on uid: 60
```

## As service <a id="installation-as-service"></a>

> ⚠️ **Manual Installation**  
> If you are not using the **Auto Upgrader**, do not forget to add `SUBVORTEX_USE_LOCAL_WORKDIR=True` in your `.env`.

To setup the Miner, you can run

```bash
./subvortex/miner/neuron/deployment/service/neuron_service_setup.sh
```

To start the Miner, you can run

```bash
./subvortex/miner/neuron/deployment/service/neuron_service_start.sh
```

To check the SubVortex Miner is up and running, you can run

```bash
systemctl status subvortex-miner-neuron
```

You should see something like

```bash
● subvortex-miner-neuron.service - SubVortex Miner Neuron
     Loaded: loaded (/etc/systemd/system/subvortex-miner-neuron.service; disabled; vendor preset: enabled)
     Active: active (running) since Tue 2025-05-06 18:58:12 CEST; 1s ago
   Main PID: 2545963 (python3)
      Tasks: 8 (limit: 19116)
     Memory: 62.9M
        CPU: 1.854s
     CGroup: /system.slice/subvortex-miner-neuron.service
             └─2545963 /root/SubVortex2/subvortex/miner/neuron/venv/bin/python3 -m subvortex.miner.neuron.src.main --subtensor.network local --use.local.workdir --wallet.hotkey default --axon.ip 127.0.0.1 --axon.port 8091 --net>

May 06 18:58:12 vmi1561561.contaboserver.net systemd[1]: Started SubVortex Miner Neuron.
```

## As docker container <a id="installation-as-container"></a>

> **IMPORTANT** <br />
> Before starting, be sure docker is installed if you decide to run the subtensor as docker container, see [docker installation](../../scripts/docker/README.md)

If you are not using the Auto Upgrader, you have to prefix all these commands by

```bash
export SUBVORTEX_FLOATTING_FLAG=latest
```

For testnet, you can use `latest` (release) or `stable` (release candidate).

To build the Miner, you can run

```bash
./subvortex/miner/neuron/deployment/docker/neuron_docker_setup.sh
```

To start the Miner, you can run

```bash
./subvortex/miner/neuron/deployment/docker/neuron_docker_start.sh
```

To check the SubVortex Miner is up and running, you can run

```bash
docker ps
```

You should see a container named `subvortex-miner-neuron`.

You can even check the logs, by running

```bash
docker logs subvortex-miner-neuron
```

You should see something like

```bash
2025-05-02 11:55:28.402 |      DEBUG       | miner version 3.0.0
2025-05-02 11:55:28.404 |      DEBUG       | [File Monitoring] started
ColdKey for the wallet 'miner' already exists.
HotKey for the wallet 'miner' already exists.
2025-05-02 11:55:28.427 |      DEBUG       | loading wallet
2025-05-02 11:55:28.434 |      DEBUG       | wallet: Wallet (Name: 'miner', Hotkey: 'default', Path: '~/.bittensor/wallets/')
2025-05-02 11:55:28.434 |      DEBUG       | loading subtensor
2025-05-02 11:55:28.435 |      DEBUG       | Connecting to network: local, chain_endpoint: ws://127.0.0.1:9944> ...
2025-05-02 11:55:30.091 |      DEBUG       | Network: local, Chain: ws://127.0.0.1:9944
2025-05-02 11:55:30.093 |      DEBUG       | checking wallet registration
2025-05-02 11:55:30.105 |      DEBUG       | loading metagraph
2025-05-02 11:55:30.607 |      DEBUG       | metagraph(netuid:7, n:256, block:4444047, network:finney)
2025-05-02 11:55:30.609 |       INFO       | Running miner on uid: 60
```

<br />

# Uninstall

## As process <a id="uninstall-as-process"></a>

To uninstall the Miner, you can run

```bash
./subvortex/miner/neuron/deployment/process/neuron_process_teardown.sh
```

To check the SubVortex Miner has been uninstalled, you can run

```bash
pm2 list
```

You should not see any process named `subvortex-miner-neuron`.

## As service <a id="uninstall-as-service"></a>

To uninstall the Miner, you can run

```bash
./subvortex/miner/neuron/deployment/service/neuron_service_teardown.sh
```

To check the SubVortex Miner has been uninstalled, you can run

```bash
systemctl status subvortex-miner-neuron
```

You should see something like

```bash
Unit subvortex-miner-neuron.service could not be found.
```

## As docker container <a id="uninstall-as-container"></a>

If you are not using the Auto Upgrader, you have to prefix all these commands by

```bash
export SUBVORTEX_FLOATTING_FLAG=latest
```

To uninstall the Miner, you can run

```bash
./subvortex/miner/neuron/deployment/docker/neuron_docker_teardown.sh
```

To check the SubVortex Miner has been uninstalled, you can run

```bash
docker ps
```

You should not see any container named `subvortex-miner-neuron`.

<br />

# Querier

The **Querier** is a CLI tool to inspect and analyze the current state of Redis-synced neurons or scores. It supports filters, sorting, column selection, and pagination to help navigate large datasets efficiently.

To run the Querier, use:

```bash
./subvortex/miner/neuron/scripts/neuron_querier.sh --namespace=<neuron|score> [options]
```

---

### ✅ Basic Usage

Query all neurons:

```bash
./subvortex/miner/neuron/scripts/neuron_querier.sh --namespace=neuron
```

Query all scores:

```bash
./subvortex/miner/neuron/scripts/neuron_querier.sh --namespace=score
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
./subvortex/miner/neuron/scripts/neuron_querier.sh --namespace=neuron --fields=uid,stake,hotkey
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
./subvortex/miner/neuron/scripts/neuron_querier.sh  --namespace=neuron --sort=-uid
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
./subvortex/miner/neuron/scripts/neuron_querier.sh \
  --namespace=neuron \
  --filter uid=60
```

#### Show all neurons from a country or multiple country

```bash
./subvortex/miner/neuron/scripts/neuron_querier.sh \
  --namespace=neuron \
  --filter country=FR \
  --fields uid,hotkey,registered_at,ip,is_serving,version
```

```bash
./subvortex/miner/neuron/scripts/neuron_querier.sh \
  --namespace=neuron \
  --filter "country in FR,ES" \
  --fields uid,hotkey,registered_at,ip,is_serving,version
```

#### Show top 10 miners

```bash
./subvortex/miner/neuron/scripts/neuron_querier.sh \
  --namespace=neuron \
  --sort=-rank \
  --page-size 10 \
  --fields uid,hotkey,country,incentive
```

#### Show validators

```bash
./subvortex/miner/neuron/scripts/neuron_querier.sh \
  --namespace=neuron \
  --sort=-dividends \
  --page-size 10 \
  --fields uid,hotkey,country,dividends \
  --filter "validator_trust>0" \
  --filter "stake>1000"
```

#### Show last 10 scores

```bash
./subvortex/miner/neuron/scripts/neuron_querier.sh \
  --namespace=score \
  --sort=-block \
  --page-size 10
```
