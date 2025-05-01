# Miner Redis Guide

This document provides a comprehensive guide on how to set up and run the miner redis. Redis is used the miner redis and miner proxy to manage the rate limit based on plan subscription.

<br />

---

- [Installation](#installation)
  - [As process](#installation-as-process)
  - [As service](#installation-as-service)
  - [As container](#installation-as-container)
- [Uninstall](#uninstall)
  - [As process](#uninstall-as-process)
  - [As service](#uninstall-as-service)
  - [As container](#uninstall-as-container)

---

<br />

# Installation

Before getting started, you need to create an .env file with the correct configuration. To generate it, run

```
cp .env.template .env
```

Then, open `.env` in a text editor and update it with your settings.

## As process <a id="installation-as-process"></a>

To setup the miner redis, you can run

```
./miner/redis/deployment/process/redis_process_setup.sh
```

To start the miner redis, you can run

```
./miner/redis/deployment/process/redis_process_start.sh
```

To check the miner redis is up and running, you can run

```

```

## As service <a id="installation-as-service"></a>

To setup the miner redis, you can run

```
./miner/redis/deployment/service/redis_service_setup.sh
```

To start the miner redis, you can run

```
./miner/redis/deployment/service/redis_service_start.sh
```

To check the miner redis is up and running, you can run

```

```

## As docker container <a id="installation-as-container"></a>

> **IMPORTANT** <br />
> Before starting, be sure docker is installed if you deciode to run the subtensor as docker container, see [docker installation](../../scripts/docker/README.md)

To build the miner redis, you can run

```
./miner/redis/deployment/docker/redis_docker_setup.sh
```

To start the miner redis, you can run

```
./miner/redis/deployment/docker/redis_docker_start.sh
```

To check the miner redis is up and running, you can run

```
docker ps
```

You should see a container named `miner-redis`.

<br />

# Uninstall

## As process <a id="uninstall-as-process"></a>

To uninstall the miner redis, you can run

```
./miner/redis/deployment/process/redis_process_teardown.sh
```

To check the miner redis has been uninstalled, you can run

```

```

## As service <a id="uninstall-as-service"></a>

To uninstall the miner redis, you can run

```
./miner/redis/deployment/service/redis_service_teardown.sh
```

To check the miner redis has been uninstalled, you can run

```

```

## As docker container <a id="uninstall-as-container"></a>

To uninstall the miner redis, you can run

```
./miner/redis/deployment/docker/redis_docker_teardown.sh
```

To check the miner redis has been uninstalled, you can run

```
docker ps
```

You should not see any container named `miner-redis`.
