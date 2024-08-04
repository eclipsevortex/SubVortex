The Grafana dashboard exposes multiple metrics about the hardware, os and the substrate node in order to help you making the right decision when needed.

<br />

---

- [Process](#process)
  - [Thread count](#thread-count)
  - [Thread CPU time](#thread-cpu-time)
- [Server Health](#server-health)
  - [CPU Busy](#cpu-busy)
  - [System Load (5 minutes)](#system-load-5-minutes)
  - [System Load (15 minutes)](#system-load-15-minutes)
  - [RAM Used](#ram-used)
  - [Swap Used](#swap-used)
  - [Root FS Used](#root-fs-used)
  - [CPU Cores](#cpu-cores)
  - [Uptime](#uptime)
  - [CPU Basic](#cpu-basic)
  - [Memory Basic](#memory-basic)
  - [Network Traffic Basic](#network-traffic-basic)
  - [I/O Usage Times](#io-usage-times)
- [Chain](#chain)
  - [Height of the Chain (Best, Finalized, Sync Target)](#height-of-the-chain-best-finalized-sync-target)
  - [Networking Bytes per Second (In, Out)](#networking-bytes-per-second-in-out)
  - [Block Rate](#block-rate)
  - [TXs Count](#txs-count)
  - [Peers Count](#peers-count)
  - [State Cache](#state-cache)
  - [Queued Blocks (Sync)](#queued-blocks-sync)
  - [Relative Block Production Speed](#relative-block-production-speed)
  - [Blocks Av per Min](#blocks-av-per-min)
  - [Diff (Best Block - Finalized)](#diff-best-block---finalized)
  - [Running Tasks](#running-tasks)
  - [sub_libp2p](#sub_libp2p)
  - [Sync Justifications](#sync-justifications)
  - [GRANDPA Validator Messages](#grandpa-validator-messages)

<br />

# Process

## Thread count

**Description** <br />
Shows the number of active threads for each process over time.

**Use** <br />
Helps monitor the concurrency and resource allocation of various processes. This can indicate the level of parallel processing and multitasking occurring in the system.

**Improvement** <br />
To manage thread count effectively, consider implementing thread pools to optimize thread creation and destruction, ensure proper thread lifecycle management to prevent leaks, and review the concurrency model to ensure it matches the workload requirements.

## Thread CPU time

**Description** <br />
Measures the CPU time consumed by threads of different processes. Each line in the graph represents the CPU time for threads of a specific process.

**Use** <br />
Indicates how much CPU time each thread is using, helping to identify performance bottlenecks, inefficiencies, or processes that are consuming excessive CPU resources.

**Improvement** <br />
To reduce CPU time, optimize the code to make it more efficient, use more efficient algorithms and data structures, distribute the workload more evenly across threads, and implement caching and memoization strategies to reduce redundant computations.

<br />

# Server Health

## CPU Busy

**Description** <br />
Shows the percentage of CPU being actively used.

**Use** <br />
Indicates how much of the CPU's capacity is being utilized.

**Improvement** <br />
To reduce CPU usage, optimize your applications, upgrade your CPU, or distribute the load across more servers.

## System Load (5 minutes)

**Description** <br />
The average load on the system over the last 5 minutes.

**Use** <br />
Helps gauge how busy the system is over a short time frame.

**Improvement** <br />
Similar to CPU usage, improve software efficiency, balance the load, or add more servers.

## System Load (15 minutes)

**Description** <br />
The average load on the system over the last 15 minutes.

**Use** <br />
Provides a slightly longer-term view of system activity.

**Improvement** <br />
Same as the 5-minute load—optimize, distribute load, or scale up your infrastructure.

## RAM Used

**Description** <br />
Percentage of RAM currently in use.

**Use** <br />
Indicates how much memory is being utilized.

**Improvement** <br />
Increase RAM capacity, optimize applications to use less memory, or restart services to clear memory leaks.

## Swap Used

**Description** <br />
Percentage of swap space in use.

**Use** <br />
Swap space is used when RAM is full. High swap usage can slow down your
system.

**Improvement** <br />
Add more RAM, reduce the number of running applications, or optimize memory usage of your applications.

## Root FS Used

**Description** <br />
Percentage of root filesystem (disk space) in use.

**Use** <br />
Shows how much of your main storage is occupied.

**Improvement** <br />
Clear unnecessary files, move data to other storage solutions, or increase disk capacity.

## CPU Cores

**Description** <br />
Number of CPU cores available.

**Use** <br />
Determines the processing capacity of your system.

**Improvement** <br />
Not applicable as this is a fixed hardware specification.

## Uptime

**Description** <br />
The amount of time the system has been running since the last reboot.

**Use** <br />
Indicates system stability and reliability.

**Improvement** <br />
Regularly update and maintain the system to avoid crashes and unscheduled reboots.

## CPU Basic

**Description** <br />
A detailed view of CPU usage over time, broken down by system, user, iowait, IRQs, etc.

**Use** <br />
Helps identify specific types of CPU usage.

**Improvement** <br />
Focus on optimizing the processes or services that are consuming the most CPU.

## Memory Basic

**Description** <br />
Detailed view of memory usage over time, showing total, used, free, and cached memory.

**Use** <br />
Provides insight into memory consumption patterns.

**Improvement** <br />
Similar to RAM used—upgrade RAM, optimize applications, or restart services to clear memory leaks.

## Network Traffic Basic

**Description** <br />
Shows incoming and outgoing network traffic over time for different interfaces.

**Use** <br />
Helps monitor network usage and detect potential bottlenecks.

**Improvement** <br />
Optimize network-heavy applications, upgrade network hardware, or balance traffic across multiple interfaces.

## I/O Usage Times

**Description** <br />
Shows the time spent on input/output operations, which can indicate disk usage performance.

**Use** <br />
Helps identify disk performance issues.

**Improvement** <br />
Upgrade to faster disks (e.g., SSDs), optimize applications to reduce I/O operations, or balance I/O load across multiple disks.

<br />

# Chain

## Height of the Chain (Best, Finalized, Sync Target)

**Description** <br />
Displays the block height of the best, finalized, and sync target blocks in the blockchain.

**Use** <br />
Helps to understand the current status of the blockchain synchronization.

**Improvement** <br />
Ensure nodes are properly synced by checking network connections and node configurations.

## Networking Bytes per Second (In, Out)

**Description** <br />
Shows the incoming and outgoing network traffic in bytes per second.

**Use** <br />
Helps monitor the network usage and detect potential network bottlenecks.

**Improvement** <br />
Optimize network infrastructure or application settings to handle higher network loads.

## Block Rate

**Description** <br />
Indicates the number of blocks produced per minute.

**Use** <br />
Monitors the blockchain's block production rate.

**Improvement** <br />
Investigate and resolve issues if the block rate is lower than expected.

## TXs Count

**Description** <br />
Shows the number of transactions processed.

**Use** <br />
Helps track the transaction throughput of the blockchain.

**Improvement** <br />
Optimize transaction processing mechanisms or increase node capacity.

## Peers Count

**Description** <br />
Displays the number of peers connected to the node.

**Use** <br />
Ensures the node is well-connected within the network.

**Improvement** <br />
Improve network connectivity or peer discovery settings.

## State Cache

**Description** <br />
Shows the usage of the state cache over time.

**Use** <br />
Monitors how much memory is used for caching blockchain state.

**Improvement** <br />
Increase cache size or optimize cache management.

## Queued Blocks (Sync)

**Description** <br />
Displays the number of blocks waiting to be synchronized.

**Use** <br />
Helps to understand synchronization backlog.

**Improvement** <br />
Optimize sync processes or increase node processing power.

## Relative Block Production Speed

**Description** <br />
Shows the ratio of block production speed over different time intervals.

**Use** <br />
Helps identify changes in block production efficiency.

**Improvement** <br />
Investigate and address reasons for slower block production.

## Blocks Av per Min

**Description** <br />
Indicates the average number of blocks available per minute.

**Use** <br />
Monitors the average block availability in the network.

**Improvement** <br />
Ensure stable block production and availability.

## Diff (Best Block - Finalized)

**Description** <br />
Shows the difference between the best block and the finalized block.

**Use** <br />
Helps track the lag between the latest block and the finalized block.

**Improvement** <br />
Optimize the finalization process to reduce this difference.

## Running Tasks

**Description** <br />
Displays the number of various running tasks like import queue, informant, etc.

**Use** <br />
Helps monitor the active tasks and their performance.

**Improvement** <br />
Optimize task management or increase node resources.

## sub_libp2p

TODO

## Sync Justifications

**Description** <br />
Displays the number of synchronization justifications.

**Use** <br />
Helps monitor the sync justification process.

**Improvement** <br />
Ensure efficient and accurate sync processes.

## GRANDPA Validator Messages

**Description** <br />
Shows the number of GRANDPA validator messages like catch_up_request, commit, etc.

**Use** <br />
Monitors the communication and consensus messages between validators.

**Improvement** <br />
Optimize validator communication and ensure proper consensus mechanism operation.
