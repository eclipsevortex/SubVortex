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

# Installation

Before getting started, you need to create an .env file with the correct configuration. To generate it, run

```
cp .env.template .env
```

Then, open `.env` in a text editor and update it with your settings.

## As process <a id="installation-as-process"></a>

To setup the SubVortex Validator, you can run

```
./neuron/deployment/process/neuron_process_setup.sh
```

To start the SubVortex Validator, you can run

```
./neuron/deployment/process/neuron_process_start.sh
```

To check the SubVortex Validator is up and running, you can run

```
pm2 log subvortex-Validator
```

You should see something like

```bash

```

## As service <a id="installation-as-service"></a>

To setup the SubVortex Validator, you can run

```
./neuron/deployment/service/neuron_service_setup.sh
```

To start the SubVortex Validator, you can run

```
./neuron/deployment/service/neuron_service_start.sh
```

To check the SubVortex Validator is up and running, you can run

```
systemctl status subvortex-validator-neuron
```

You should see something like

```bash

```

## As docker container <a id="installation-as-container"></a>

> **IMPORTANT** <br />
> Before starting, be sure docker is installed if you deciode to run the subtensor as docker container, see [docker installation](../../scripts/docker/README.md)

To build the SubVortex Validator, you can run

```
./neuron/deployment/docker/neuron_docker_setup.sh
```

To start the SubVortex Validator, you can run

```
./neuron/deployment/docker/neuron_docker_start.sh
```

To check the SubVortex Validator is up and running, you can run

```
docker ps
```

You should see a container named `subvortex-validator-neuron`.

<br />

# Uninstall

## As process <a id="uninstall-as-process"></a>

To uninstall the SubVortex Validator, you can run

```
./neuron/deployment/process/neuron_process_teardown.sh
```

To check the SubVortex Validator has been uninstalled, you can run

```
pm2 list
```

You should not see any process named `subvortex-Validator`.

## As service <a id="uninstall-as-service"></a>

To uninstall the SubVortex Validator, you can run

```
./neuron/deployment/service/neuron_service_teardown.sh
```

To check the SubVortex Validator has been uninstalled, you can run

```
systemctl status subvortex-validator-neuron
```

You should see something like

```
Unit subvortex-validator-neuron.service could not be found.
```

## As docker container <a id="uninstall-as-container"></a>

To uninstall the SubVortex Validator, you can run

```
./neuron/deployment/docker/neuron_docker_teardown.sh
```

To check the SubVortex Validator has been uninstalled, you can run

```
docker ps
```

You should not see any container named `subvortex-validator-neuron`.
