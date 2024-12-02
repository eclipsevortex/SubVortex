[Back to Main README](../../README.md)

This document explains how to install and uninstall the subnet SubVortex.

<br />

---

- [Installation](#intasllation)
- [Uninstallation](#uninstallation)
- [Migration](#migration)
  - [Migrate](#migration-migrate)
  - [Downgrade](#migration-downgrade)

---

<br />

# Installation

Before installing the subnet, you have to install some prerequisites

```
# Update package manager
apt-get update

# Install git
apt-get install -y git

# Install pip
apt-get install -y python3-pip
```

Then, you have to clone the **SubVortex** repository

```
# Go to HOME directory
cd $HOME

# Clone the subnet
git clone https://github.com/eclipsevortex/SubVortex.git
```

Finally, to install the subnet, you can run

```
# Go to SubVortex
cd SubVortex

# Setup the subnet
./scripts/subnet/subnet_setup.sh
```

<br />

# Uninstallation

To uninstall the subnet, you can run

```
./SubVortex/scripts/subnet/subnet_teardown.sh
```

Be sure you are in the **SubVortex's** parent directory

# Migration

## Migrate <a id="migration-migrate"></a>

To uprade the Subnet manually, you can use the python script `subnet_upgrade.py`.

For example, if you are on tag v2.2.2 and want to migrate to the tag v2.2.3, you can run in `SubVortex`

```
python3 ./scripts/subnet/utils/subnet_upgrade.py --tag v2.2.3
```

## Downgrade <a id="migration-downgrade"></a>

To downgrade the Subnet manually, you can use the python script `subnet_upgrade.py`.

For example, if you are on tag v2.2.3 and want to downgrade to the tag v2.2.2, you can run in `SubVortex`

```
python3 ./scripts/subnet/utils/subnet_upgrade.py --tag v2.2.2
```
