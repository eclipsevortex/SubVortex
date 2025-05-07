# Validator Guide

This document provides a comprehensive guide on how to quick start/stop the Miner components.

<br />

---

- [Pre-requisites](#pre-requisites)
- [Quick Start](#quick-start)
- [Quick Stop](#quick-stop)

---

<br />

> ⚠️ **Architecture Notice**  
> The Miner currently supports only **x86_64 (amd64)** servers.  
> `arm64` support is not yet available but is a work in progress.

<br />

# Pre-requisites

Before getting started, you need to create an .env file with the correct configuration for each components of the Miner. To generate it, go to subvortex > miner > neuron and run

```bash
cp .env.template .env
```

Then, open `.env` in a text editor and update it with your settings.

Do the same for redis

# Quick Start

To setup and start the Miner and its components, you can run

```bash
./subvortex/miner/scripts/quick_start.sh
```

The Miner and Redis should be installed and start successfully

For more details on the options, run

```bash
./subvortex/miner/scripts/quick_start.sh -h
```

# Quick Stop

To stop and teardown the Miner and its components, you can run

```bash
./subvortex/miner/scripts/quick_stop.sh
```

The Miner and Redis should stop and be cleaned successfully

For more details on the options, run

```bash
./subvortex/miner/scripts/quick_stop.sh -h
```
