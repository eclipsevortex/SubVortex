[Back to Main README](../../README.md)

Grafana is used to create and customize dashboards for visualizing the metrics collected by Prometheus, providing an intuitive and powerful interface for monitoring your system performance.

<br />

---

- [Installation](#installation)
- [Uninstallation](#uninstallation)

# Installation

To install Grafana, run:

```bash
./scripts/grafana/grafana_setup.sh
```

Next, start it with:

```bash
./scripts/grafana/grafana_start.sh
```

# Uninstallation

To uninstall Grafana, first stop the service:

```bash
./scripts/grafana/grafana_stop.sh
```

Then, you can uninstall it by running:

```bash
./scripts/grafana/grafana_teardown.sh
```
