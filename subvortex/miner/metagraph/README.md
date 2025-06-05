# SubVortex Miner Metagraph Guide

This document provides a comprehensive guide on how to set up and run the Metagraph Metagraph. The metagraph is used to sync data from the metagraph and persist them to redis.

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
> The Metagraph currently supports only **x86_64 (amd64)** servers.  
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
> Before starting, be sure pm2 is installed if you decide to run the Metagraph in a process, see [pm2 installation](../../../scripts/process/README.md)

To setup the Metagraph, you can run

```bash
./subvortex/miner/metagraph/deployment/process/neuron_process_setup.sh
```

To start the Metagraph, you can run

```bash
./subvortex/miner/metagraph/deployment/process/neuron_process_start.sh
```

To check the Metagraph is up and running, you can run

```bash
pm2 log subvortex-miner-metagraph
```

You should see something like

```bash
266|subvor | 2025-06-05 04:20:29.251 |       INFO       | Debug enabled.
266|subvor | 2025-06-05 04:20:29.252 |       INFO       | Settings: Settings(logging_name='Metagraph', key_prefix='sv', netuid=92, sync_interval=100, dry_run=False, database_host='localhost', database_port=6379, database_index=0, database_password='')
266|subvor | 2025-06-05 04:20:29.253 |      DEBUG       | Version: 3.1.4
266|subvor | 2025-06-05 04:20:29.253 |     WARNING      | Metagraph - ⏳ Waiting for Redis to become available...
266|subvor | 2025-06-05 04:20:29.262 |       INFO       | Metagraph - ✅ Connected to Redis.
266|subvor | 2025-06-05 04:20:29.263 |      DEBUG       | Connecting to network: local, chain_endpoint: ws://127.0.0.1:9944...
266|subvor | 2025-06-05 04:20:29.270 |       INFO       | Connecting to Substrate: Network: local, Chain: ws://127.0.0.1:9944...
266|subvor | 2025-06-05 04:20:30.530 |       INFO       | Network: local, Chain: ws://127.0.0.1:9944
266|subvor | 2025-06-05 04:20:30.530 |       INFO       | metagraph(netuid:92, n:0, block:0, network:local)
266|subvor | 2025-06-05 04:20:30.530 |       INFO       | Metagraph - 🚀 MetagraphObserver service starting...

266|subvortex-miner-metagraph  | 2025-06-05 04:20:36.865 |       INFO       | Metagraph - 📦 Block #4685973 detected
266|subvortex-miner-metagraph  | 2025-06-05 04:20:36.881 |       INFO       | Metagraph - 🔄 Syncing neurons due to periodic sync interval reached.
266|subvortex-miner-metagraph  | 2025-06-05 04:20:37.771 |      DEBUG       | Metagraph - 📡 Full metagraph sync complete
266|subvortex-miner-metagraph  | 2025-06-05 04:20:38.032 |      DEBUG       | Metagraph - 💾 Neurons loaded from Redis: 199
```

And at some point, you should see

```bash
266|subvortex-miner-metagraph  | 2025-06-05 04:20:38.038 |      DEBUG       | Metagraph - 🔔 Metagraph marked ready
266|subvortex-miner-metagraph  | 2025-06-05 04:20:38.042 |      DEBUG       | Metagraph - 📣 Broadcasting metagraph ready state
266|subvortex-miner-metagraph  | 2025-06-05 04:20:48.543 |       INFO       | Metagraph - 📦 Block #4685974 detected
```

## As service <a id="installation-as-service"></a>

> ⚠️ **Manual Installation**  
> If you are not using the **Auto Upgrader**, do not forget to add `SUBVORTEX_USE_LOCAL_WORKDIR=True` in your `.env`.

To setup the Metagraph, you can run

```bash
./subvortex/miner/metagraph/deployment/service/neuron_service_setup.sh
```

To start the Metagraph, you can run

```bash
./subvortex/miner/metagraph/deployment/service/neuron_service_start.sh
```

To check the Metagraph is up and running, you can run

```bash
systemctl status subvortex-miner-metagraph
```

You should see something like

```bash
● subvortex-miner-metagraph.service - SubVortex Miner Metagraph
     Loaded: loaded (/etc/systemd/system/subvortex-miner-metagraph.service; disabled; vendor preset: enabled)
     Active: active (running) since Thu 2025-06-05 04:23:57 CEST; 2min 16s ago
   Main PID: 3673235 (python3)
      Tasks: 9 (limit: 19116)
     Memory: 141.5M
        CPU: 31.941s
     CGroup: /system.slice/subvortex-miner-metagraph.service
             └─3673235 /root/SubVortex/subvortex/miner/metagraph/venv/bin/python3 -m subvortex.miner.metagraph.src.main

Jun 05 04:23:57 vmi1561561.contaboserver.net systemd[1]: Started SubVortex Miner Metagraph.
```

And check the log by running

```
tail -f /var/log/subvortex-miner/subvortex-miner-metagraph.log
```

```bash
2025-06-05 04:23:59.103 |       INFO       | bittensor:loggingmachine.py:423 | Debug enabled.
2025-06-05 04:23:59.105 |       INFO       | Settings: Settings(logging_name='Metagraph', key_prefix='sv', netuid=92, sync_interval=100, dry_run=False, database_host='localhost', database_port=6379, database_index=0, database_password='')
2025-06-05 04:23:59.105 |      DEBUG       | Version: 3.1.4
2025-06-05 04:23:59.106 |     WARNING      | Metagraph - ⏳ Waiting for Redis to become available...
2025-06-05 04:23:59.110 |       INFO       | Metagraph - ✅ Connected to Redis.
2025-06-05 04:23:59.111 |      DEBUG       | Connecting to network: local, chain_endpoint: ws://127.0.0.1:9944...
2025-06-05 04:23:59.115 |       INFO       | Connecting to Substrate: Network: local, Chain: ws://127.0.0.1:9944...
2025-06-05 04:24:00.862 |       INFO       | Network: local, Chain: ws://127.0.0.1:9944
2025-06-05 04:24:00.862 |       INFO       | metagraph(netuid:92, n:0, block:0, network:local)
2025-06-05 04:24:00.862 |       INFO       | Metagraph - 🚀 MetagraphObserver service starting...
2025-06-05 04:24:01.233 |       INFO       | Metagraph - 📦 Block #4685990 detected
2025-06-05 04:24:01.250 |       INFO       | Metagraph - 🔄 Syncing neurons due to periodic sync interval reached.
2025-06-05 04:24:02.564 |      DEBUG       | Metagraph - 📡 Full metagraph sync complete
2025-06-05 04:24:03.394 |      DEBUG       | Metagraph - 💾 Neurons loaded from Redis: 199
```

And at some point, you should see

```bash
2025-06-05 04:24:03.404 |      DEBUG       | Metagraph - 🔔 Metagraph marked ready
2025-06-05 04:24:03.409 |      DEBUG       | Metagraph - 📣 Broadcasting metagraph ready state
2025-06-05 04:24:12.711 |       INFO       | Metagraph - 📦 Block #4685991 detected
```

## As docker container <a id="installation-as-container"></a>

> **IMPORTANT** <br />
> Before starting, be sure docker is installed if you decide to run the subtensor as docker container, see [docker installation](../../scripts/docker/README.md)

If you are not using the Auto Upgrader, you have to prefix all these commands by

```bash
export SUBVORTEX_FLOATTING_FLAG=latest
```

For testnet, you can use `latest` (release) or `stable` (release candidate).

To build the Metagraph, you can run

```bash
./subvortex/miner/metagraph/deployment/docker/neuron_docker_setup.sh
```

To start the Metagraph, you can run

```bash
./subvortex/miner/metagraph/deployment/docker/neuron_docker_start.sh
```

To check the Metagraph is up and running, you can run

```bash
docker ps
```

You should see a container named `subvortex-miner-metagraph`.

You can even check the logs, by running

```bash
docker logs subvortex-miner-metagraph
```

You should see something like

```bash
2025-06-05 02:29:23.504 |       INFO       | bittensor:loggingmachine.py:423 | Debug enabled.
2025-06-05 02:29:24.465 |       INFO       | bittensor:loggingmachine.py:410 | Enabling debug.
2025-06-05 02:29:24.465 |       INFO       | Debug enabled.
2025-06-05 02:29:24.466 |       INFO       | Settings: Settings(logging_name='Metagraph', key_prefix='sv', netuid=92, sync_interval=100, dry_run=False, database_host='localhost', database_port=6379, database_index=0, database_password='')
2025-06-05 02:29:24.467 |      DEBUG       | Version: 3.1.4
2025-06-05 02:29:24.467 |     WARNING      | Metagraph - ⏳ Waiting for Redis to become available...
2025-06-05 02:29:24.467 |     WARNING      | Metagraph - Reconnecting to Redis...
2025-06-05 02:29:24.467 |       INFO       | Metagraph - Connected to Redis
2025-06-05 02:29:24.475 |       INFO       | Metagraph - ✅ Connected to Redis.
2025-06-05 02:29:24.475 |      DEBUG       | Connecting to network: local, chain_endpoint: ws://127.0.0.1:9944...
2025-06-05 02:29:24.480 |       INFO       | Connecting to Substrate: Network: local, Chain: ws://127.0.0.1:9944...
2025-06-05 02:29:25.688 |       INFO       | Network: local, Chain: ws://127.0.0.1:9944
2025-06-05 02:29:25.688 |       INFO       | metagraph(netuid:92, n:0, block:0, network:local)
2025-06-05 02:29:25.688 |       INFO       | Metagraph - 🚀 MetagraphObserver service starting...
2025-06-05 02:29:36.666 |       INFO       | Metagraph - 📦 Block #4686018 detected
2025-06-05 02:29:36.680 |       INFO       | Metagraph - 🔄 Syncing neurons due to periodic sync interval reached.
2025-06-05 02:29:37.351 |      DEBUG       | Metagraph - 📡 Full metagraph sync complete
2025-06-05 02:29:37.526 |      DEBUG       | Metagraph - 💾 Neurons loaded from Redis: 199
```

And at some point, you should see

```bash
2025-06-05 02:29:37.561 |      DEBUG       | Metagraph - 🔔 Metagraph marked ready
2025-06-05 02:29:37.565 |      DEBUG       | Metagraph - 📣 Broadcasting metagraph ready state
2025-06-05 02:29:48.798 |       INFO       | Metagraph - 📦 Block #4686019 detected
```

<br />

# Uninstall

## As process <a id="uninstall-as-process"></a>

To uninstall the Metagraph, you can run

```bash
./subvortex/miner/metagraph/deployment/process/neuron_process_teardown.sh
```

To check the Metagraph has been uninstalled, you can run

```bash
pm2 list
```

You should not see any process named `subvortex-miner-metagraph`.

## As service <a id="uninstall-as-service"></a>

To uninstall the Metagraph, you can run

```bash
./subvortex/miner/metagraph/deployment/service/neuron_service_teardown.sh
```

To check the Metagraph has been uninstalled, you can run

```bash
systemctl status subvortex-miner-metagraph
```

You should see something like

```bash
Unit subvortex-miner-metagraph.service could not be found.
```

## As docker container <a id="uninstall-as-container"></a>

If you are not using the Auto Upgrader, you have to prefix all these commands by

```bash
export SUBVORTEX_FLOATTING_FLAG=latest
```

To uninstall the Metagraph, you can run

```bash
./subvortex/miner/metagraph/deployment/docker/neuron_docker_teardown.sh
```

To check the Metagraph has been uninstalled, you can run

```bash
docker ps
```

You should not see any container named `subvortex-miner-metagraph`.

<br />

# Querier

The **Querier** is a CLI tool to inspect and analyze the current state of Redis-synced neurons. It supports filters, sorting, column selection, and pagination to help navigate large datasets efficiently.

To run the Querier, use:

```bash
./subvortex/miner/metagraph/scripts/metagraph_querier.sh --namespace=neuron [options]
```

---

### ✅ Basic Usage

Query all neurons:

```bash
./subvortex/miner/metagraph/scripts/metagraph_querier.sh --namespace=neuron
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
./subvortex/miner/metagraph/scripts/metagraph_querier.sh --namespace=neuron --fields=uid,stake,hotkey
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
./subvortex/miner/metagraph/scripts/metagraph_querier.sh  --namespace=neuron --sort=-uid
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
./subvortex/miner/metagraph/scripts/metagraph_querier.sh \
  --namespace=neuron \
  --filter uid=60
```

#### Show all neurons from a country or multiple country

```bash
./subvortex/miner/metagraph/scripts/metagraph_querier.sh \
  --namespace=neuron \
  --filter country=FR \
  --fields uid,hotkey,registered_at,ip,is_serving,version
```

```bash
./subvortex/miner/metagraph/scripts/metagraph_querier.sh \
  --namespace=neuron \
  --filter "country in FR,ES" \
  --fields uid,hotkey,registered_at,ip,is_serving,version
```

#### Show top 10 miners

```bash
./subvortex/miner/metagraph/scripts/metagraph_querier.sh \
  --namespace=neuron \
  --sort=-rank \
  --page-size 10 \
  --fields uid,hotkey,country,incentive
```

#### Show validators

```bash
./subvortex/miner/metagraph/scripts/metagraph_querier.sh \
  --namespace=neuron \
  --sort=-dividends \
  --page-size 10 \
  --fields uid,hotkey,country,dividends \
  --filter "validator_trust>0" \
  --filter "stake>1000"
```
