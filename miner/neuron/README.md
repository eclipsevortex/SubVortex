This document explains how to install/uninstall the miner

<br />

---

- [Installation](#installation)
  - [As process](#installation-as-process)
  - [As docker container](#installation-as-container)
- [Uninstallation](#uninstallation)
  - [As process](#uninstallation-as-process)
  - [As docker container](#uninstallation-as-container)

---

<br />

# Installation

Before getting started, you need to create an .env file with the correct configuration. To generate it, run

```
cp .env.template .env
```

Then, open `.env` in a text editor and update it with your settings.

## As process <a id="installation-as-process"></a>

To setup the miner, you can run

```
./miner/neuron/deployment/process/neuron_process_setup.sh
```

To start the miner, you can run

```
./miner/neuron/deployment/process/neuron_process_start.sh
```

To check the miner is up and running, you can run

```

```

## As docker container <a id="installation-as-container"></a>

> **IMPORTANT** <br />
> Before starting, be sure docker is installed if you deciode to run the subtensor as docker container, see [docker installation](../../scripts/docker/README.md)

To setup the miner, you can run

```
./miner/neuron/deployment/docker/neuron_docker_setup.sh
```

To start the miner, you can run

```
./miner/neuron/deployment/docker/neuron_docker_start.sh
```

To check the miner is up and running, you can run

```
docker ps
```

You should see a container named `miner`.

# Uninstallation

## As process <a id="uninstallation-as-process"></a>

To uninstall the miner, you can run

```
./miner/miner/deployment/process/neuron_process_teardown.sh
```

To check the miner has been uninstalled, you can run

```

```

## As docker container <a id="uninstallation-as-container"></a>

To uninstall the miner, you can run

```
./miner/neuron/deployment/docker/neuron_docker_teardown.sh
```

To check the miner has been uninstalled, you can run

```
docker ps
```

You should not see any container named `miner`.
