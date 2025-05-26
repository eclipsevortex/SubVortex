# SubVortex Validator Metagraph Guide

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
./subvortex/validator/metagraph/deployment/process/neuron_process_setup.sh
```

To start the Metagraph, you can run

```bash
./subvortex/validator/metagraph/deployment/process/neuron_process_start.sh
```

To check the Metagraph is up and running, you can run

```bash
pm2 log subvortex-validator-metagraph
```

You should see something like

```bash
```

## As service <a id="installation-as-service"></a>

> ⚠️ **Manual Installation**  
> If you are not using the **Auto Upgrader**, do not forget to add `SUBVORTEX_USE_LOCAL_WORKDIR=True` in your `.env`.

To setup the Metagraph, you can run

```bash
./subvortex/validator/metagraph/deployment/service/neuron_service_setup.sh
```

To start the Metagraph, you can run

```bash
./subvortex/validator/metagraph/deployment/service/neuron_service_start.sh
```

To check the Metagraph is up and running, you can run

```bash
systemctl status subvortex-validator-metagraph
```

You should see something like

```bash
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
./subvortex/validator/metagraph/deployment/docker/neuron_docker_setup.sh
```

To start the Metagraph, you can run

```bash
./subvortex/validator/metagraph/deployment/docker/neuron_docker_start.sh
```

To check the Metagraph is up and running, you can run

```bash
docker ps
```

You should see a container named `subvortex-validator-metagraph`.

You can even check the logs, by running

```bash
docker logs subvortex-validator-metagraph
```

You should see something like

```bash
```

<br />

# Uninstall

## As process <a id="uninstall-as-process"></a>

To uninstall the Metagraph, you can run

```bash
./subvortex/validator/metagraph/deployment/process/neuron_process_teardown.sh
```

To check the Metagraph has been uninstalled, you can run

```bash
pm2 list
```

You should not see any process named `subvortex-validator-metagraph`.

## As service <a id="uninstall-as-service"></a>

To uninstall the Metagraph, you can run

```bash
./subvortex/validator/metagraph/deployment/service/neuron_service_teardown.sh
```

To check the Metagraph has been uninstalled, you can run

```bash
systemctl status subvortex-validator-metagraph
```

You should see something like

```bash
Unit subvortex-validator-metagraph.service could not be found.
```

## As docker container <a id="uninstall-as-container"></a>

If you are not using the Auto Upgrader, you have to prefix all these commands by

```bash
export SUBVORTEX_FLOATTING_FLAG=latest
```

To uninstall the Metagraph, you can run

```bash
./subvortex/validator/metagraph/deployment/docker/neuron_docker_teardown.sh
```

To check the Metagraph has been uninstalled, you can run

```bash
docker ps
```

You should not see any container named `subvortex-validator-metagraph`.
