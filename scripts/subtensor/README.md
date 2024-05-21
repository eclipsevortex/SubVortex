[Back to Main README](../../README.md)

This document explains how to install and uninstall a local subtensor.

<br />

---

- [Installation](#intasllation)
  - [As process](#installation-as-process)
  - [As docker container](#installation-as-container)
- [Uninstallation](#uninstallation)
  - [As process](#uninstallation-as-process)
  - [As docker container](#uninstallation-as-container)
- [Troubleshooting](#troubleshooting)

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

<br />

# Troubleshooting

## Impossible to sync my subtensor

If you have one the following tracks, follow the steps to solve your issue at the end of this section

```
2024-05-14 09:19:10 Corrupted state at `[38, 170, 57, 78, 234, 86, 48, 224, 124, 72, 174, 12, 149, 88, 206, 247, 185, 157, 136, 14, 198, 129, 121, 156, 12, 243, 14, 136, 134, 55, 29, 169, 131, 182, 193, 67, 70, 115, 122, 160, 171, 172, 230, 73, 147, 75, 49, 23, 204, 202, 200, 132, 219, 205, 30, 6, 79, 226, 145, 110, 177, 217, 6, 178, 167, 123, 168, 121, 90, 59, 72, 19, 29, 141, 78, 66, 8, 75, 147, 116]: Error`
2024-05-14 09:19:10 Corrupted state at `[38, 170, 57, 78, 234, 86, 48, 224, 124, 72, 174, 12, 149, 88, 206, 247, 185, 157, 136, 14, 198, 129, 121, 156, 12, 243, 14, 136, 134, 55, 29, 169, 236, 78, 143, 40, 0, 22, 190, 30, 170, 238, 16, 63, 121, 36, 44, 169, 94, 223, 118, 216, 213, 244, 13, 161, 228, 51, 111, 138, 5, 31, 63, 188, 253, 83, 172, 115, 135, 219, 241, 46, 238, 103, 80, 122, 199, 220, 116, 126]: Error`
2024-05-14 09:19:10 Corrupted state at `[38, 170, 57, 78, 234, 86, 48, 224, 124, 72, 174, 12, 149, 88, 206, 247, 185, 157, 136, 14, 198, 129, 121, 156, 12, 243, 14, 136, 134, 55, 29, 169, 83, 23, 62, 117, 11, 93, 103, 147, 111, 53, 29, 172, 18, 159, 113, 238, 68, 29, 32, 161, 190, 131, 245, 148, 204, 199, 206, 127, 200, 67, 165, 180, 180, 176, 51, 154, 138, 142, 188, 46, 149, 55, 225, 14, 77, 192, 243, 31]: Error`
```

Or

```
2024-05-14 09:20:21 Detected prevote equivocation in the finality worker: Equivocation { round_number: 17111820, identity: Public(c8a00ef71912b3868b101cb70ebd029999d1c9b6a1390122a98f60d72b9a0fc4 (5Gbkysfa...)), first: (Prevote { target_hash: 0xe7ac73730c6d310d8c8335090c2603eb83fef286adadd90a54afecbd3af84cf3, target_number: 1881111 }, Signature(5b2216349275831f77f6d3c98a30d779bd240fbdb27e116ecdf4b2bfe5cbedfe45cd27706b19251cb8020378e0bc25c0bd4c6611ec922fbe20a412b8161c8a01)), second: (Prevote { target_hash: 0x040e64d10de745f832bbe0db9247db043339f6a3f67afcbb13c1c7031e7e7475, target_number: 1881162 }, Signature(f806a2dc7293fa1823f12746fa2fd19f605ed0e406c3bc59c4d839e3f335b6042b997331168b53066e7164638dee33df1f91c0fe32289b4b21e20490d2853d0b)) }
2024-05-14 09:20:21 Detected prevote equivocation in the finality worker: Equivocation { round_number: 17111820, identity: Public(b57a038c9139a060358f3b654df74a1cb6d15bcdb8438bcebd64ce67ec4301eb (5GAemcU4...)), first: (Prevote { target_hash: 0xe7ac73730c6d310d8c8335090c2603eb83fef286adadd90a54afecbd3af84cf3, target_number: 1881111 }, Signature(61149cbef647b2311673060e6bccb80936d667ab7bfd28bc3d6042f366756a93a4744d3b18409d738395dac4198ebea028220a83715bc0dcf3ff45ee19bd690c)), second: (Prevote { target_hash: 0x040e64d10de745f832bbe0db9247db043339f6a3f67afcbb13c1c7031e7e7475, target_number: 1881162 }, Signature(95b3c0b15bbb99ae460a7d5e570d2b9a84f86000eb31d085f03ceeb5a96905698a119712a15599e407a56d1d801310411126cb3384bb678d1be87e48bd05c50e)) }
```

Or

You do not see any

```
2024-05-14 09:27:58 ✨ Imported #1918032 (0xf3a8…edf8)
```

It seems you have an issue of sync your local subtensor.

To resolve the issue with docker

- Stop the subtensor - `docker stop subtensor-NETWORK-lite` (NETWORK can be testnet or mainnet)
- Get the Mountpoint of the volume - `docker volume inspect subtensor_NETWORK-lite-volume` (NETWORK can be testnet or mainnet)
- Remove the state of the blockchain - `rm -rf MOUNTPOINT/*` (MOUNTPOINT is the one you got in the previous step)
- Restart the subtensor - `docker start subtensor-NETWORK-lite` (NETWORK can be testnet or mainnet)
- Check the logs - `docker logs subtensor-NETWORK-lite -f` (NETWORK can be testnet or mainnet)

To resolve the issue with process

- Stop the subtensor - `pm2 stop subtensor`
- Remove the state of the blockchain - `rm -rf /tmp/blockchain`
- Restart the subtensor - `pm2 start subtensor`
- Check the logs - `pm2 logs subtensor`

Once your subtensor has restarted, you will see a bunch of logs like below, it can take few minutes to resync everything.

```
2024-05-14 09:27:33 Successfully ran block step.
2024-05-14 09:27:33 Successfully ran block step.
2024-05-14 09:27:33 Successfully ran block step.
2024-05-14 09:27:33 Successfully ran block step.
```

And at some point, you will see normal logs such as

```
2024-05-14 09:27:58 ✨ Imported #1918032 (0xf3a8…edf8)
```

## Others

If you have any issues, refer to the [official documentation](https://docs.bittensor.com/subtensor-nodes/) or the [official github](https://github.com/opentensor/subtensor)
