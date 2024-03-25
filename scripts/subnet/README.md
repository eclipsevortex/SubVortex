[Back to Main README](../../README.md)

This document explains how to install and uninstall the subnet SubVortex.

# Installation

Before installing the subnet, you have to install some prerequisites

```
# Update package manager
apt-get update

# Install git
apt-get install git

# Install pip
apt-get install python3-pip
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
./scripts/subnet/subnet_setup.sh
```

Be sure you are in **SubVortex** directory

<br />

# Uninstallation

To uninstall the subnet, you can run

```
./SubVortex/scripts/subnet/subnet_teardown.sh
```

Be sure you are in the **SubVortex's** parent directory