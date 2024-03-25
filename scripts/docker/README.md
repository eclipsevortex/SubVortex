[Back to Main README](../../README.md)

This document explains how to install docker in your machine.

> Note: Before starting, be sure you are in `SubVortex` directory

<br />

---

- [Installation](#intasllation)
  - [Macos](#installation-macos)
  - [Linux](#installation-linux)
- [Uninstallation](#uninstallation)
  - [Macos](#uninstallation-macos)
  - [Linux](#uninstallation-linux)

---

<br />

# Installation

## Macos <a id="installation-macos"></a>

To install Docker on macOS, you can follow these steps:

### Download Docker Desktop

Go to the Docker website (https://www.docker.com/products/docker-desktop) and download Docker Desktop for Mac.

### Install Docker Desktop

Once the download is complete, open the downloaded file (Docker.dmg) and drag the Docker icon to the Applications folder to install it.

### Launch Docker Desktop

Open Docker Desktop from the Applications folder or from Launchpad.

### Start Docker

After launching Docker Desktop, it may prompt you for your system password to complete the installation process. Once the installation is complete, Docker Desktop should start automatically. You should see the Docker icon in the menu bar.

### Verify Installation

To verify that Docker is installed correctly, open a terminal window and run the following command:

```
docker --version
```

This command should display the version of Docker that is installed on your system.

To verify that Docker compose is installed correctly, open a terminal window and run the following command:

```
docker-compose --version
```

This command should display the version of Docker compose that is installed on your system.

## Linux <a id="installation-linux"></a>

To install docker on Linus, you have to run

```
./scripts/docker/docker_setup.sh
```

This script will install docker and docker-compose.

To check everything is installed, you can check the version of docker

```
docker -v
```

This command should display the version of Docker that is installed on your system.

You can check as well the version of docker compose

```
docker-compose -v
```

This command should display the version of Docker that is installed on your system.

<br />

# Uninstallation

## Macos <a id="uninstallation-macos"></a>

To uninstall Docker Desktop on macOS, you can follow these steps:

### Quit Docker Desktop

First, ensure that Docker Desktop is not running. You can quit Docker Desktop by clicking on the Docker icon in the menu bar and selecting "Quit Docker Desktop".

### Uninstall Docker Desktop

Open a terminal window and run the following command:

```
/Applications/Docker.app/Contents/MacOS/Docker --uninstall
```

This command removes Docker Desktop and all associated components from your system.

### Remove Docker Desktop Application

Next, you can manually remove the Docker Desktop application from your Applications folder. You can do this by dragging the Docker application to the Trash.

### Remove Docker Data

Optionally, you may also want to remove Docker data, including containers, images, volumes, and settings. Be cautious with this step as it will permanently delete all Docker-related data. You can remove the Docker data directory by running:

```
rm -rf ~/Library/Containers/com.docker.docker
```

### Restart Your Mac

After uninstalling Docker Desktop and removing associated data, you may want to restart your Mac to ensure that all changes take effect.

## Linux <a id="uninstallation-linux"></a>

To uninstall docker, you have to run

```
./scripts/docker/docker_teardown.sh
```

To check everything is uninstalled, you can check the following command failed

```
docker -v
```

You should get something similar to

```
bash: /usr/bin/docker: No such file or directory
```

You can check as well

```
docker-compose -v
```

You should get something similar to

```
bash: /usr/bin/docker-compose: No such file or directory
```
