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
