[Back to Main README](../../README.md)

This document explains how to install and configure wandb

<br />

---

- [Installation](#intasllation)
- [Configuration](#configuration)
  - [Validator](#configuration-validator)
  - [Miner](#configuration-miner)
- [User Guide](#user-guide)
- [Troubleshooting](#troubleshooting)

---

<br />

# Installation

**Step 1: Installation of wandb**

This install of wandb is included when installing the SubVortex subnet (see the [guide](../../scripts/subnet/README.md) for installation details)

You can check wandb is installing by executing in **SubVortex** directory

```
pip show wandb
```

You have to see something like

```
Name: wandb
Version: 0.16.5
Summary: A CLI and library for interacting with the Weights & Biases API.
Home-page:
Author:
Author-email: Weights & Biases <support@wandb.com>
License: MIT License
```

<br />

**Step 2: Obtain Your API Key**

1. Log in to your Weights & Biases account through your web browser.
2. Go to your account settings, usually accessible from the top right corner under your profile.
3. Find the section labeled "API keys".
4. Copy your API key. It's a long string of characters unique to your account.

<br />

**Step 3: Setting Up the API Key in Ubuntu**

Log into wandb by executing

```
wandb login
```

You are going to be asked to provide your api key

```
wandb: Logging into wandb.ai. (Learn how to deploy a W&B server locally: https://wandb.me/wandb-server)
wandb: You can find your API key in your browser here: https://wandb.ai/authorize
wandb: Paste an API key from your profile and hit enter, or press ctrl+c to quit:
```

<br />

# Configuration

## Validator

The default configuration is enough to have a good user experience so there is no real need to update it.

The default configuration will create a maximum of 2 runs (active + one archive) containing 360 steps of data. We chose 360, which corresponds to an epoch, and we believe it is sufficient to understand the trend and adjust the subtensor accordingly.

Options

- `--wandb.off` - turn off wandb. Default **false**
- `--wandb.project_name` - The name of the project where you are sending the new run. Default is **subvortex-team** for mainnet and **test-subvortex-team** for testnet
- `--wandb.entity` - An entity is a username or team name where youre sending runs. Default is **eclipsevortext**
- `--wandb.offline` - Runs wandb in offline mode. Default **false**
- `--wandb.run_step_length` - How many steps before we rollover to a new run. Default **360**

## Miner

For miner, wandb is not needed so nothing to do here.

<br />

# User Guide

## Miners

The table display the list of miners with the following informations
- `` - 
- `` -
- `` -
- `` -
- `` -

From that table, you can get a quick overview of how you are competing with others. You can sort the different columns to prioritize the desired information. We are still investigating if filtering is possible with Wandb.

## Localisation

The histogram gives you the number of subtensors per country. Based on how the distribution score is computed, you can easily identify a country where there are no subtensors or a very small number, in order to maximize it.

## Scores



<br />

# Troubleshooting

None