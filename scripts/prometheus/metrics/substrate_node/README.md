[Back to Main README](../../README.md)

Substrate node is used by Prometheus to collect and expose substrate node metrics.

<br />

---

- [Installation](#installation)
- [Uninstallation](#uninstallation)

# Installation

To install Substrate Node, run:

```bash
./scripts/prometheus/metrics/substrate_node/substrate_node_setup.sh
```

Next, start it with:

```bash
./scripts/prometheus/metrics/substrate_node/substrate_node_start.sh
```

# Uninstallation

To uninstall Substrate Node, first stop the service:

```bash
./scripts/prometheus/metrics/substrate_node/substrate_node_stop.sh
```

Then, you can uninstall it by running:

```bash
./scripts/prometheus/metrics/substrate_node/substrate_node_teardown.sh
```
