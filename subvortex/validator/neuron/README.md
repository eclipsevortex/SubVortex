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

To setup the Validator, you can run

```
./subvortex/validator/neuron/deployment/process/neuron_process_setup.sh
```

To start the Validator, you can run

```
./subvortex/validator/neuron/deployment/process/neuron_process_start.sh
```

To check the Validator is up and running, you can run

```
pm2 log subvortex-validator-neuron
```

You should see something like

```bash
2025-05-02 11:51:43.474 |      DEBUG       | validator version 3.0.0
2025-05-02 11:51:43.474 |      DEBUG       | loading wallet
2025-05-02 11:51:43.475 |      DEBUG       | loading subtensor
2025-05-02 11:51:43.475 |      DEBUG       | Connecting to network: finney, chain_endpoint: wss://entrypoint-finney.opentensor.ai:443> ...
2025-05-02 11:51:45.444 |      DEBUG       | Network: test, Chain: wss://entrypoint-finney.opentensor.ai:443
2025-05-02 11:51:45.501 |      DEBUG       | wallet: Wallet (Name: 'subvortex', Hotkey: 'default', Path: '~/.bittensor/wallets/')
2025-05-02 11:51:45.502 |      DEBUG       | loading metagraph
2025-05-02 11:51:46.356 |      DEBUG       | metagraph(netuid:7, n:256, block:4444028, network:finney)
```

## As service <a id="installation-as-service"></a>

To setup the Validator, you can run

```
./subvortex/validator/neuron/deployment/service/neuron_service_setup.sh
```

To start the Validator, you can run

```
./subvortex/validator/neuron/deployment/service/neuron_service_start.sh
```

To check the Validator is up and running, you can run

```
systemctl status subvortex-validator-neuron
```

You should see something like

```bash
2025-05-02 11:51:43.474 |      DEBUG       | validator version 3.0.0
2025-05-02 11:51:43.474 |      DEBUG       | loading wallet
2025-05-02 11:51:43.475 |      DEBUG       | loading subtensor
2025-05-02 11:51:43.475 |      DEBUG       | Connecting to network: finney, chain_endpoint: wss://entrypoint-finney.opentensor.ai:443> ...
2025-05-02 11:51:45.444 |      DEBUG       | Network: test, Chain: wss://entrypoint-finney.opentensor.ai:443
2025-05-02 11:51:45.501 |      DEBUG       | wallet: Wallet (Name: 'subvortex', Hotkey: 'default', Path: '~/.bittensor/wallets/')
2025-05-02 11:51:45.502 |      DEBUG       | loading metagraph
2025-05-02 11:51:46.356 |      DEBUG       | metagraph(netuid:7, n:256, block:4444028, network:finney)
```

## As docker container <a id="installation-as-container"></a>

> **IMPORTANT** <br />
> Before starting, be sure docker is installed if you deciode to run the subtensor as docker container, see [docker installation](../../../scripts/docker/README.md)

To build the Validator, you can run

```
./subvortex/validator/neuron/deployment/docker/neuron_docker_setup.sh
```

To start the Validator, you can run

```
./subvortex/validator/neuron/deployment/docker/neuron_docker_start.sh
```

To check the Validator is up and running, you can run

```
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
2025-05-02 11:51:45.444 |      DEBUG       | Network: test, Chain: wss://entrypoint-finney.opentensor.ai:443
2025-05-02 11:51:45.501 |      DEBUG       | wallet: Wallet (Name: 'subvortex', Hotkey: 'default', Path: '~/.bittensor/wallets/')
2025-05-02 11:51:45.502 |      DEBUG       | loading metagraph
2025-05-02 11:51:46.356 |      DEBUG       | metagraph(netuid:7, n:256, block:4444028, network:finney)
```

<br />

# Uninstall

## As process <a id="uninstall-as-process"></a>

To uninstall the Validator, you can run

```
./subvortex/validator/neuron/deployment/process/neuron_process_teardown.sh
```

To check the Validator has been uninstalled, you can run

```
pm2 list
```

You should not see any process named `subvortex-Validator`.

## As service <a id="uninstall-as-service"></a>

To uninstall the Validator, you can run

```
./subvortex/validator/neuron/deployment/service/neuron_service_teardown.sh
```

To check the Validator has been uninstalled, you can run

```
systemctl status subvortex-validator-neuron
```

You should see something like

```
Unit subvortex-validator-neuron.service could not be found.
```

## As docker container <a id="uninstall-as-container"></a>

To uninstall the Validator, you can run

```
./subvortex/validator/neuron/deployment/docker/neuron_docker_teardown.sh
```

To check the Validator has been uninstalled, you can run

```
docker ps
```

You should not see any container named `subvortex-validator-neuron`.
