[Back to Main README](../../README.md)

This document explains how to install pm2 on your machine.

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

To install PM2 on Macos, you have to run

```
./scripts/process/process_setup.sh
```

To check everything is installed, you can check the version of docker

```
pm2 --version
```

This command should display the version of PM2.

## Linux <a id="installation-linux"></a>

To install PM2 on Macos, you have to run

```
./scripts/process/process_setup.sh
```

To check everything is installed, you can check the version

```
pm2 --version
```

This command should display the version of PM2.

<br />

# Uninstallation

## Macos <a id="uninstallation-macos"></a>

To uninstall PM2 on Macos, you have to run

```
./scripts/process/process_teardown.sh
```

To check everything is uninstalled, you can run

```
pm2 --version
```

You should get a not found message

## Linux <a id="uninstallation-linux"></a>

To uninstall PM2 on Macos, you have to run

```
./scripts/process/process_teardown.sh
```

To check everything is uninstalled, you can run

```
pm2 --version
```

You should get a not found message
