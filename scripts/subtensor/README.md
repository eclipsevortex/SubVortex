This document explains how to install and uninstall a local subtensor.

<br />

---

- [Installation](#intasllation)
  - [As process](#installation-as-process)
  - [As docker container](#installation-as-container)
- [Uninstallation](#uninstallation)
  - [As process](#uninstallation-as-process)
  - [As docker container](#uninstallation-as-container)

---

<br />

# Installation

Subtensor can be install in two way

- as process in the base environment
- as container via docker

> Note: Before starting, be sure
>
> - docker is installed if you deciode to run the subtensor as docker container, see [docker installation](../docker/README.md)
> - you are in the `SubVortex` directory

## As process <a id="installation-as-process"></a>

To run a local subtensor as a process in the base environment, you are going to need all the scripts in `SubVortex/scripts/subtensor/process`.

To setup subtensor, you can run

```
./scripts/subtensor/process/subtensor_process_setup.sh
```

With the options you can see by running

```
./scripts/subtensor/process/subtensor_process_setup.sh -h
```

Then, start it, by running

```
./scripts/subtensor/process/subtensor_process_start.sh
```

With the options you can see by running

```
./scripts/subtensor/process/subtensor_process_start.sh -h
```

If you have a process manager such as pm2, use it

```
pm2 start ./scripts/subtensor/process/subtensor_process_start.sh --name subtensor
```

Once started, you can check the local subtensor is running by looking into the log

```
pm2 log subtensor
```

You shoud have something similar to

```
0|subtenso | 2024-03-19 23:31:41 🏷  Local node identity is: 12D3KooWPycx2kKpkkwbzjFSAKdTVFRvntLUKkC7VB3P7aUThmfX
0|subtenso | 2024-03-19 23:31:41 💻 Operating system: linux
0|subtenso | 2024-03-19 23:31:41 💻 CPU architecture: x86_64
0|subtenso | 2024-03-19 23:31:41 💻 Target environment: gnu
0|subtenso | 2024-03-19 23:31:41 💻 CPU: AMD EPYC 7282 16-Core Processor
0|subtenso | 2024-03-19 23:31:41 💻 CPU cores: 6
0|subtenso | 2024-03-19 23:31:41 💻 Memory: 16002MB
0|subtenso | 2024-03-19 23:31:41 💻 Kernel: 5.15.0-25-generic
0|subtenso | 2024-03-19 23:31:41 💻 Linux distribution: Ubuntu 22.04.4 LTS
0|subtenso | 2024-03-19 23:31:41 💻 Virtual machine: yes
0|subtenso | 2024-03-19 23:31:41 📦 Highest known block at #0
0|subtenso | 2024-03-19 23:31:41 〽️ Prometheus exporter started at 0.0.0.0:9615
0|subtenso | 2024-03-19 23:31:41 Running JSON-RPC HTTP server: addr=0.0.0.0:9933, allowed origins=["*"]
0|subtenso | 2024-03-19 23:31:41 Running JSON-RPC WS server: addr=0.0.0.0:9944, allowed origins=["*"]
0|subtenso | 2024-03-19 23:31:42 🔍 Discovered new external address for our node: /ip4/155.133.26.129/tcp/30333/ws/p2p/12D3KooWPycx2kKpkkwbzjFSAKdTVFRvntLUKkC7VB3P7aUThmfX
0|subtensor  | 2024-03-19 23:31:46 ⏩ Warping, Downloading state, 8.40 Mib (59 peers), best: #0 (0x2f05…6c03), finalized #0 (0x2f05…6c03), ⬇ 1.4MiB/s ⬆ 42.2kiB/s
0|subtensor  | 2024-03-19 23:31:51 ⏩ Warping, Downloading state, 48.79 Mib (74 peers), best: #0 (0x2f05…6c03), finalized #0 (0x2f05…6c03), ⬇ 4.0MiB/s ⬆ 14.2kiB/s
```

At some point you have to see some line such as the following

```
Imported #2596101 (0xfdc2…8016)
```

Be sure the **#xxxxxxxx**, which is the current block, matches the one in [polkadot](https://polkadot.js.org/apps/#/explorer)

## As docker container <a id="installation-as-container"></a>

To run a local subtensor as a docker container, you are going to need all the scripts in `SubVortex/scripts/subtensor/docker`.

To setup subtensor, you can run

```
./scripts/subtensor/docker/subtensor_docker_setup.sh
```

Then, start it, by running

```
./scripts/subtensor/docker/subtensor_docker_start.sh
```

With the options you can see by running

```
./scripts/subtensor/docker/subtensor_docker_start.sh -h
```

Once started, you can check the local subtensor is running by looking into the log

```
docker logs $(docker ps -a --format "{{.Names}}" --filter "ancestor=opentensor/subtensor:latest")
```

You shoud have something similar to

```
0|subtenso | 2024-03-19 23:31:41 🏷  Local node identity is: 12D3KooWPycx2kKpkkwbzjFSAKdTVFRvntLUKkC7VB3P7aUThmfX
0|subtenso | 2024-03-19 23:31:41 💻 Operating system: linux
0|subtenso | 2024-03-19 23:31:41 💻 CPU architecture: x86_64
0|subtenso | 2024-03-19 23:31:41 💻 Target environment: gnu
0|subtenso | 2024-03-19 23:31:41 💻 CPU: AMD EPYC 7282 16-Core Processor
0|subtenso | 2024-03-19 23:31:41 💻 CPU cores: 6
0|subtenso | 2024-03-19 23:31:41 💻 Memory: 16002MB
0|subtenso | 2024-03-19 23:31:41 💻 Kernel: 5.15.0-25-generic
0|subtenso | 2024-03-19 23:31:41 💻 Linux distribution: Ubuntu 22.04.4 LTS
0|subtenso | 2024-03-19 23:31:41 💻 Virtual machine: yes
0|subtenso | 2024-03-19 23:31:41 📦 Highest known block at #0
0|subtenso | 2024-03-19 23:31:41 〽️ Prometheus exporter started at 0.0.0.0:9615
0|subtenso | 2024-03-19 23:31:41 Running JSON-RPC HTTP server: addr=0.0.0.0:9933, allowed origins=["*"]
0|subtenso | 2024-03-19 23:31:41 Running JSON-RPC WS server: addr=0.0.0.0:9944, allowed origins=["*"]
0|subtenso | 2024-03-19 23:31:42 🔍 Discovered new external address for our node: /ip4/155.133.26.129/tcp/30333/ws/p2p/12D3KooWPycx2kKpkkwbzjFSAKdTVFRvntLUKkC7VB3P7aUThmfX
0|subtensor  | 2024-03-19 23:31:46 ⏩ Warping, Downloading state, 8.40 Mib (59 peers), best: #0 (0x2f05…6c03), finalized #0 (0x2f05…6c03), ⬇ 1.4MiB/s ⬆ 42.2kiB/s
0|subtensor  | 2024-03-19 23:31:51 ⏩ Warping, Downloading state, 48.79 Mib (74 peers), best: #0 (0x2f05…6c03), finalized #0 (0x2f05…6c03), ⬇ 4.0MiB/s ⬆ 14.2kiB/s
```

At some point you have to see some line such as the following

```
Imported #2596101 (0xfdc2…8016)
```

Be sure the **#xxxxxxxx**, which is the current block, matches the one in [polkadot](https://polkadot.js.org/apps/#/explorer)

<br />

# Uninstallation

> Note: Before starting, be sure you are in the `SubVortex` directory

## As process <a id="uninstallation-as-process"></a>

To uninstall a local subtensor, you can stop (and delete) it if running

```
pm2 stop subtensor && pm2 delete subtensor
```

Then, you can run

```
./scripts/subtensor/process/subtensor_process_teardown.sh
```

## As docker container <a id="uninstallation-as-container"></a>

To uninstall a local subtensor, you can stop (and delete) it if running

```
docker stop $(docker ps --format "{{.Names}}" --filter "ancestor=opentensor/subtensor:latest") && docker rm $(docker ps -a --format "{{.Names}}" --filter "ancestor=opentensor/subtensor:latest")
```

Then, you have to remove the subtensor image

```
docker rmi $(docker images | awk 'NR>1 {print $3}')
```

Then, you can run

```
./scripts/subtensor/docker/subtensor_docker_teardown.sh
```
