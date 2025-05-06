# Validator Redis Guide

This document provides a comprehensive guide on how to set up and run the Validator Redis. Redis is used by the validator to store miners' scores over time.

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

> ⚠️ **Architecture Notice**  
> The Validator Redis currently supports only **x86_64 (amd64)** servers.  
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
> Before starting, be sure pm2 is installed if you decide to run the Validator Redis in a process, see [pm2 installation](../../../scripts/process/README.md)

To setup the Validator Redis, you can run

```bash
./subvortex/validator/redis/deployment/process/redis_process_setup.sh
```

To start the Validator Redis, you can run

```bash
./subvortex/validator/redis/deployment/process/redis_process_start.sh
```

To check the Validator Redis is up and running, you can run

```bash
pm2 log subvortex-validator-redis
```

You should see something like

```bash
133|subvor | 770411:M 05 May 2025 17:04:30.614 * Server initialized
133|subvor | 770411:M 05 May 2025 17:04:30.615 * Reading RDB base file on AOF loading...
133|subvor | 770411:M 05 May 2025 17:04:30.615 * Loading RDB produced by version 8.0.0
133|subvor | 770411:M 05 May 2025 17:04:30.615 * RDB age 4253 seconds
133|subvor | 770411:M 05 May 2025 17:04:30.615 * RDB memory usage when created 0.92 Mb
133|subvor | 770411:M 05 May 2025 17:04:30.615 * RDB is base AOF
133|subvor | 770411:M 05 May 2025 17:04:30.615 * Done loading RDB, keys loaded: 0, keys expired: 0.
133|subvor | 770411:M 05 May 2025 17:04:30.615 * DB loaded from base file appendonly.aof.1.base.rdb: 0.000 seconds
133|subvor | 770411:M 05 May 2025 17:04:30.636 * DB loaded from incr file appendonly.aof.1.incr.aof: 0.021 seconds
133|subvor | 770411:M 05 May 2025 17:04:30.636 * DB loaded from append only file: 0.021 seconds
133|subvor | 770411:M 05 May 2025 17:04:30.639 * Opening AOF incr file appendonly.aof.1.incr.aof on server start
133|subvor | 770411:M 05 May 2025 17:04:30.639 * Ready to accept connections tcp
```

## As service <a id="installation-as-service"></a>

To setup the Validator Redis, you can run

```bash
./subvortex/validator/redis/deployment/service/redis_service_setup.sh
```

To start the Validator Redis, you can run

```bash
./subvortex/validator/redis/deployment/service/redis_service_start.sh
```

To check the Validator Redis is up and running, you can run

```bash
systemctl status subvortex-validator-redis
```

You should see something like

```bash
● subvortex-validator-redis.service - SubVortex Validator Redis
     Loaded: loaded (/etc/systemd/system/subvortex-validator-redis.service; disabled; vendor preset: enabled)
     Active: active (running) since Mon 2025-05-05 17:25:57 BST; 4s ago
       Docs: http://redis.io/documentation,
             man:redis-server(1)
   Main PID: 774498 (redis-server)
     Status: "Ready to accept connections"
      Tasks: 6 (limit: 28765)
     Memory: 3.3M
        CPU: 106ms
     CGroup: /system.slice/subvortex-validator-redis.service
             └─774498 "/usr/bin/redis-server 127.0.0.1:6379" "" "" "" "" "" "" ""

May 05 17:25:56 vmi1610615.contaboserver.net systemd[1]: Starting SubVortex Validator Redis...
May 05 17:25:57 vmi1610615.contaboserver.net systemd[1]: Started SubVortex Validator Redis.
```

## As docker container <a id="installation-as-container"></a>

> **IMPORTANT** <br />
> Before starting, be sure docker is installed if you decide to run the Validator Redis as docker container, see [docker installation](../../scripts/docker/README.md)

If you are not using the Auto Upgrader, you have to prefix all these commands by

```bash
export SUBVORTEX_FLOATTING_FLAG=latest
```

To build the Validator Redis, you can run

```bash
./subvortex/validator/redis/deployment/docker/redis_docker_setup.sh
```

To start the Validator Redis, you can run

```bash
./subvortex/validator/redis/deployment/docker/redis_docker_start.sh
```

To check the Validator Redis is up and running, you can run

```bash
docker ps
```

You should see a container named `subvortex-validator-redis`.

<br />

# Uninstall

## As process <a id="uninstall-as-process"></a>

To uninstall the Validator Redis, you can run

```bash
./subvortex/validator/redis/deployment/process/redis_process_teardown.sh
```

To check the Validator Redis has been uninstalled, you can run

```bash
pm2 list
```

You should not see any process named `subvortex-validator-redis`.

## As service <a id="uninstall-as-service"></a>

To uninstall the Validator Redis, you can run

```bash
./subvortex/validator/redis/deployment/service/redis_service_teardown.sh
```

To check the Validator Redis has been uninstalled, you can run

```bash
systemctl status subvortex-validator-redis
```

You should see something like

```bash
Unit subvortex-validator-redis.service could not be found.
```

## As docker container <a id="uninstall-as-container"></a>

If you are not using the Auto Upgrader, you have to prefix all these commands by

```bash
export SUBVORTEX_FLOATTING_FLAG=latest
```

To uninstall the Validator Redis, you can run

```bash
./subvortex/validator/redis/deployment/docker/redis_docker_teardown.sh
```

To check the Validator Redis has been uninstalled, you can run

```bash
docker ps
```

You should not see any container named `subvortex-validator-redis`.
