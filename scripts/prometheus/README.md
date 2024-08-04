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
- [Alerts](#alerts)
- [UI](#ui)

<br />

# Installation

To install Prometheus, run:

```bash
./scripts/prometheus/prometheus_setup.sh
```

Next, start it with:

```bash
./scripts/prometheus/prometheus_start.sh
```

To check the service is up and running

```bash
sudo systemctl status prometheus
```

You should see something like

```bash
● prometheus.service - Prometheus Server
     Loaded: loaded (/etc/systemd/system/prometheus.service; enabled; vendor preset: enabled)
     Active: active (running) since Mon 2024-07-08 21:26:44 CEST; 9s ago
   Main PID: 341640 (prometheus)
      Tasks: 10 (limit: 19117)
     Memory: 18.0M
        CPU: 139ms
     CGroup: /system.slice/prometheus.service
             └─341640 /usr/local/bin/prometheus --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/var/lib/prometheus --web.console.templates=>

Jul 08 21:26:44 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:26:44.889Z caller=head.go:479 component=tsdb msg="Replaying on-d>
Jul 08 21:26:44 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:26:44.889Z caller=head.go:513 component=tsdb msg="On-disk memory>
Jul 08 21:26:44 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:26:44.889Z caller=head.go:519 component=tsdb msg="Replaying WAL,>
Jul 08 21:26:44 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:26:44.889Z caller=head.go:590 component=tsdb msg="WAL segment lo>
Jul 08 21:26:44 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:26:44.889Z caller=head.go:596 component=tsdb msg="WAL replay com>
Jul 08 21:26:44 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:26:44.892Z caller=main.go:849 fs_type=EXT4_SUPER_MAGIC
Jul 08 21:26:44 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:26:44.892Z caller=main.go:852 msg="TSDB started"
Jul 08 21:26:44 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:26:44.892Z caller=main.go:979 msg="Loading configuration file" f>
Jul 08 21:26:44 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:26:44.893Z caller=main.go:1016 msg="Completed loading of configu>
Jul 08 21:26:44 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:26:44.893Z caller=main.go:794 msg="Server is ready to receive we
```

Some metrics can be added

- For Monitoring machine metrics, please refer to [Node Exporter Guide](./metrics/node_exporter/README.md)
- For Substrate metrics, please refer to [Subtsrate Guide](./metrics/substrate_node/README.md)
- For Process metrics, please refer to [Process Exporter Guide](./metrics/process_exporter/README.md)

Some alerts can be added, please refer to [Alert Guide](./alerts/README.md)

<br />

# Uninstallation

To uninstall Prometheus, first stop the service:

```bash
./scripts/prometheus/prometheus_stop.sh
```

To check the service is down

```bash
sudo systemctl status prometheus
```

You should see something like

```bash
○ prometheus.service - Prometheus Server
     Loaded: loaded (/etc/systemd/system/prometheus.service; disabled; vendor preset: enabled)
     Active: inactive (dead)

Jul 08 21:28:25 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:28:25.790Z caller=main.go:705 msg="Notify discovery manager stop>
Jul 08 21:28:25 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:28:25.790Z caller=manager.go:936 component="rule manager" msg="S>
Jul 08 21:28:25 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:28:25.790Z caller=manager.go:946 component="rule manager" msg="R>
Jul 08 21:28:25 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:28:25.790Z caller=main.go:725 msg="Scrape manager stopped"
Jul 08 21:28:25 vmi1561561.contaboserver.net systemd[1]: Stopping Prometheus Server...
Jul 08 21:28:25 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:28:25.792Z caller=notifier.go:601 component=notifier msg="Stoppi>
Jul 08 21:28:25 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:28:25.792Z caller=main.go:906 msg="Notifier manager stopped"
Jul 08 21:28:25 vmi1561561.contaboserver.net prometheus[341640]: level=info ts=2024-07-08T19:28:25.792Z caller=main.go:918 msg="See you next time!"
Jul 08 21:28:25 vmi1561561.contaboserver.net systemd[1]: prometheus.service: Deactivated successfully.
Jul 08 21:28:25 vmi1561561.contaboserver.net systemd[1]: Stopped Prometheus Server.
```

Then, you can uninstall it by running:

```bash
./scripts/prometheus/prometheus_teardown.sh
```

Metrics can be removed

- For Monitoring machine metrics, please refer to [Node Exporter Guide](./metrics/node_exporter/README.md)
- For Substrate metrics, please refer to [Subtsrate Guide](./metrics/substrate_node/README.md)
- For Process metrics, please refer to [Process Exporter Guide](./metrics/process_exporter/README.md)

Alerts can be removed, please refer to [Alert Guide](./alerts/README.md)

<br />

# Metrics

Some relevant metrics can be added to your neuron

- Node Exporter - to monitor hardware and OS metrics
- Substrate Node - to monitor substrate node metrics

To install Node Exporter, refer to the [Node Exporter Guide](./metrics/node_exporter/README.md)
To install Substrate Node, refer to the [Substrate Node Guide](./metrics/substrate_node/README.md)

<br />

# Alerts

Some alerts can be added to be notified when something is going wrong.

To install these alerts, refer to the [Alert Guide](./alerts/README.md)

<br />

# UI

To visualize all these metrics collected, Grafana can be used. To install is, refer to the [Grafana guide](../grafana/README.md)
