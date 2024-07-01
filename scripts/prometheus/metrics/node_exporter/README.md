[Back to Main README](../../README.md)

Node exporter is used by Prometheus to collect and expose hardware and OS metrics.

<br />

---

- [Installation](#installation)
- [Uninstallation](#uninstallation)

# Installation

To install Node Exporter, run:

```bash
./scripts/prometheus/metrics/node_exporter/node_exporter_setup.sh
```

Next, start it with:

```bash
./scripts/prometheus/metrics/node_exporter/node_exporter_start.sh
```

# Uninstallation

To uninstall Node Exporter, first stop the service:

```bash
./scripts/prometheus/metrics/node_exporter/node_exporter_stop.sh
```

Then, you can uninstall it by running:

```bash
./scripts/prometheus/metrics/node_exporter/node_exporter_teardown.sh
```
