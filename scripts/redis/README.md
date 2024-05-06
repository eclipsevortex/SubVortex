[Back to Main README](../../README.md)

This document explains how to install and uninstall a redis.

<br />

---

- [Installation](#intasllation)
  - [As process](#installation-as-process)
  - [As docker container](#installation-as-container)
- [Uninstallation](#uninstallation)
  - [As process](#uninstallation-as-process)
  - [As docker container](#uninstallation-as-container)
- [Migration](#migration)
  - [Rollout](#migration-rollout)
  - [Rollback](#migration-rollback)
- [Dump](#migration)
  - [Creation](#dump-creation)
  - [Restoration](#dump-restoration)

---

> IMPORTANT: DO NOT install redis via docker for now as we need more time to make it works!

<br />

# Installation

Redis can be install in two way

- as process in the base environment
- as container via docker

> Note: Before starting, be sure
>
> - docker is installed if you deciode to run redis as docker container, see [docker installation](../docker/README.md)
> - you are in the `SubVortex` directory

## As process <a id="installation-as-process"></a>

To run a redis instance as a process in the base environment, you are going to need all the scripts in `SubVortex/scripts/redis/process`.

To setup redis, you can run

```
./scripts/redis/process/redis_process_setup.sh
```

With the options you can see by running

```
./scripts/redis/process/redis_process_setup.sh -h
```

The below script will

- Install redis on the machine
- Protect with password
- Disable snapshots and enable AOF
- Configure the firewall

If you want to run a specific script, just execute it

```
./scripts/redis/scripts/redis_set_firewall.sh
```

> Note: some scripts may have option, so add `-h` to check them if exist

Once redis is installed, you can check redis health by executing the ping by executing

```
./scripts/redis/process/redis_process_health_check.sh
```

With the options you can see by running

```
./scripts/redis/process/redis_process_health_check.sh -h
```

For the password, you can get it by running

```
sudo grep -Po '^requirepass \K.*' /etc/redis/redis.conf
```

So the test health command will be

```
./scripts/redis/process/redis_process_health_check.sh -a $(sudo grep -Po '^requirepass \K.*' /etc/redis/redis.conf)
```

To check redis is up and running, you can check the logs as well by running

```
cat /var/log/redis/redis-server.log
```

You have to see somethinng similar to

```
1:C 19 Mar 2024 09:29:11.137 # WARNING Memory overcommit must be enabled! Without it, a background save or replication may fail under low memory condition. Being disabled, it can also 590672:C 19 Mar 2024 17:51:23.756 * oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
590672:C 19 Mar 2024 17:51:23.756 * Redis version=7.2.4, bits=64, commit=00000000, modified=0, pid=590672, just started
590672:C 19 Mar 2024 17:51:23.756 * Configuration loaded
590672:M 19 Mar 2024 17:51:23.756 * monotonic clock: POSIX clock_gettime
590672:M 19 Mar 2024 17:51:23.757 * Running mode=standalone, port=6379.
590672:M 19 Mar 2024 17:51:23.757 # Warning: Could not create server TCP listening socket ::1:6379: bind: Cannot assign requested address
590672:M 19 Mar 2024 17:51:23.759 * Server initialized
590672:M 19 Mar 2024 17:51:23.761 * Creating AOF base file appendonly.aof.1.base.rdb on server start
590672:M 19 Mar 2024 17:51:23.762 * Creating AOF incr file appendonly.aof.1.incr.aof on server start
590672:M 19 Mar 2024 17:51:23.762 * Ready to accept connections tcp
```

<br />

## As docker container <a id="installation-as-container"></a>

To run a redis instance as a docker container, you are going to need all the scripts in `SubVortex/scripts/redis/docker`.

To setup redis, you can run

```
./scripts/redis/docker/redis_docker_setup.sh
```

The below script will

- Install redis as docker container
- Protect with password
- Disable snapshots and enable AOF
- Configure the firewall

If you want to run a specific script, you have to start an interactive shell session

```
docker exec -it <CONTAINER_NAME> /bin/sh
```

Then, execute the script the same way you will do on your own machine

```
./scripts/redis/scripts/redis_set_firewall.sh
```

Finally, to quit the shell session, execute **CTRL + C**

> Note: some scripts may have option, so add `-h` to check them if exist

Once redis is installed, you can start it

```
./scripts/redis/docker/redis_docker_start.sh
```

With the options you can see by running

```
./scripts/redis/docker/redis_docker_start.sh -h
```

Once redis is started, you can check redis health by executing the ping by executing

```
./scripts/redis/docker/redis_docker_health_check.sh
```

With the options you can see by running

```
./scripts/redis/docker/redis_docker_health_check.sh -h
```

For the password, you can get it by running

```
docker exec -it subvortex-redis /bin/sh -c "grep -Eo '^requirepass[[:space:]]+(.*)$' /etc/redis/redis.conf | awk '{print \$2}'"
```

To check redis is up and running, you can check the logs as well by running

```
docker logs subvortex-redis
```

You have to see somethinng similar to

```
1:C 19 Mar 2024 09:29:11.137 # WARNING Memory overcommit must be enabled! Without it, a background save or replication may fail under low memory condition. Being disabled, it can also cause failures without low memory condition, see https://github.com/jemalloc/jemalloc/issues/1328. To fix this issue add 'vm.overcommit_memory = 1' to /etc/sysctl.conf and then reboot or run the command 'sysctl vm.overcommit_memory=1' for this to take effect.
1:C 19 Mar 2024 09:29:11.137 * oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
1:C 19 Mar 2024 09:29:11.137 * Redis version=7.2.4, bits=64, commit=00000000, modified=0, pid=1, just started
1:C 19 Mar 2024 09:29:11.137 * Configuration loaded
1:M 19 Mar 2024 09:29:11.138 * monotonic clock: POSIX clock_gettime
1:M 19 Mar 2024 09:29:11.139 # Failed to write PID file: Permission denied
1:M 19 Mar 2024 09:29:11.140 * Running mode=standalone, port=6379.
1:M 19 Mar 2024 09:29:11.140 # Warning: Could not create server TCP listening socket ::1:6379: bind: Address not available
1:M 19 Mar 2024 09:29:11.140 * Server initialized
1:M 19 Mar 2024 09:29:11.142 * Creating AOF base file appendonly.aof.1.base.rdb on server start
1:M 19 Mar 2024 09:29:11.143 * Creating AOF incr file appendonly.aof.1.incr.aof on server start
1:M 19 Mar 2024 09:29:11.143 * Ready to accept connections tcp
```

<br />

# Uninstallation

> Note: Before starting, be sure you are in the `SubVortex` directory

## As process <a id="uninstallation-as-process"></a>

To uninstall redis, you can run

```
./scripts/redis/process/redis_process_teardown.sh
```

Once redis is uninstalled, you can check redis cli does not exist anymore

```
redis-cli
```

You should have an error like this

```
command not found: redis-cli
```

## As docker container <a id="uninstallation-as-container"></a>

To uninstall redis, you can run

```
./scripts/redis/docker/redis_docker_teardown.sh
```

Once redis is uninstalled, you can check the container does not exist anymore

```
docker ps --filter name=subvortex-redis
```

You shoud have something similar (or at least list that does not container `subvortex`)

```
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

Besides, you can check every related images have been removed

```
docker images --filter reference=subvortex-redis
```

You shoud have something similar (or at least list that does not container `subvortex`)

```
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

# Migration

## Rollout <a id="migration-rollout"></a>

To rollout any Redis migration manually, you can use the python script `redis_migration.py`.

For example, if you want to rollout the version 2.2.1, you can run in `SubVortex`

```
python3 ./scripts/redis/utils/redis_migration.py --run-type rollout --version 2.2.1
```

> IMPORTANT <br />
> If you have to rollout multiple versions, execute them one by one from your current version to the targeted one.

## Rollback <a id="migration-rollback"></a>

To rollback any Redis migration manually, you can use the python script `redis_migration.py`.

For example, if you want to rollback the version 2.2.1, you can run in `SubVortex`

```
python3 ./scripts/redis/utils/redis_migration.py --run-type rollback --version 2.2.1
```

> IMPORTANT <br />
> If you have to rollback multiple versions, execute them one by one from your current version to the targeted one.

# Dump

## Creation <a id="dump-creation"></a>

To create a Redis dump manually, you can use the python script `redis_dump.py`.

For example, if you want to create the dump in the `subVortex` directory, you can run

```
python3 ./scripts/redis/utils/redis_dump.py --run-type create
```

If you want to create the dump in another location and/or name, you can use the argument `--dump-path`

```
python3 ./scripts/redis/utils/redis_dump.py --run-type create --dump-path /tmp/redis/redis-dump-2.0.0.json
```

## Restoration <a id="dump-restoration"></a>

To restore a Redis dump manually, you can use the python script `redis_dump.py`.

For example, if you want to create in `subVortex` directory, you can run

```
python3 ./scripts/redis/utils/redis_dump.py --run-type restore
```

If you want to restore a dump in another location, you can use the argument `--dump-path`

```
python3 ./scripts/redis/utils/redis_dump.py --run-type restore --dump-path /tmp/redis
```
