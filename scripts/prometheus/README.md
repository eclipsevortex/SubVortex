[Back to Main README](../../README.md)

Prometheus is a powerful tool for monitoring and visualizing the performance metrics of your applications and infrastructure in real-time.

You can use Prometheus to:

1. Monitor machine metrics via `node_exporter`.
2. Monitor Substrate metrics via `subtensor_node`.

<br />

---

- [Installation](#installation)
- [Uninstallation](#uninstallation)
- [Metrics](#metrics)
- [UI](#ui)

# Installation

To install Prometheus, run:

```bash
./scripts/prometheus/prometheus_setup.sh
```

Next, start it with:

```bash
./scripts/prometheus/prometheus_start.sh
```

Some metrics can be added

- For monitoring machine metrics, please refer to [Node Exporter Guide](./metrics//node_exporter/README.md)
- For Substrate metrics, please refer to [Subtsrate Guide](./metrics//substrate_node//README.md)

Finally, you can

# Uninstallation

To uninstall Prometheus, first stop the service:

```bash
./scripts/prometheus/prometheus_stop.sh
```

Then, you can uninstall it by running:

```bash
./scripts/prometheus/prometheus_teardown.sh
```

# Metrics

Some relevant metrics can be added to your neuron

- Node Exporter - to monitor hardware and OS metrics
- Substrate Node - to monitor substrate node metrics

To install Node Exporter, refer to the [Node Exporter Guide](./metrics/node_exporter/README.md)
To install Substrate Node, refer to the [Substrate Node Guide](./metrics/substrate_node/README.md)

# UI

To visualize all these metrics collected, Grafana can be used. To install is, refer to the [Grafana guide](../grafana/README.md)
