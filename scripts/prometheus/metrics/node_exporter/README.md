[Back to Prometheus](../../README.md)

Node exporter is used by Prometheus to collect and expose hardware and OS metrics.

<br />

---

- [Installation](#installation)
- [Uninstallation](#uninstallation)

<br />

# Installation

To install Node Exporter, run:

```bash
./scripts/prometheus/metrics/node_exporter/node_exporter_setup.sh
```

Next, start it with:

```bash
./scripts/prometheus/metrics/node_exporter/node_exporter_start.sh
```

To check the service is up and running

```bash
sudo systemctl status node_exporter
```

You should see something like

```bash
● node_exporter.service - Node Exporter
     Loaded: loaded (/etc/systemd/system/node_exporter.service; enabled; vendor preset: enabled)
     Active: active (running) since Mon 2024-07-08 21:29:55 CEST; 8s ago
   Main PID: 342561 (node_exporter)
      Tasks: 5 (limit: 19117)
     Memory: 2.5M
        CPU: 17ms
     CGroup: /system.slice/node_exporter.service
             └─342561 /usr/local/bin/node_exporter

Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=thermal_zone
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=time
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=timex
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=udp_queues
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=uname
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=vmstat
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=xfs
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=zfs
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:199 level=info msg="Listening on" add>
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.935Z caller=tls_config.go:195 level=info msg="TLS is disabled." ht>
```

<br />

# Uninstallation

To uninstall Node Exporter, first stop the service:

```bash
./scripts/prometheus/metrics/node_exporter/node_exporter_stop.sh
```

Then, you can uninstall it by running:

```bash
./scripts/prometheus/metrics/node_exporter/node_exporter_teardown.sh
```

To check the service is down

```bash
sudo systemctl status node_exporter
```

You should see something like

```bash
○ node_exporter.service - Node Exporter
     Loaded: loaded (/etc/systemd/system/node_exporter.service; disabled; vendor preset: enabled)
     Active: inactive (dead)

Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=udp_queues
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=uname
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=vmstat
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=xfs
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:115 level=info collector=zfs
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.934Z caller=node_exporter.go:199 level=info msg="Listening on" add>
Jul 08 21:29:55 vmi1561561.contaboserver.net node_exporter[342561]: ts=2024-07-08T19:29:55.935Z caller=tls_config.go:195 level=info msg="TLS is disabled." ht>
Jul 08 21:31:11 vmi1561561.contaboserver.net systemd[1]: Stopping Node Exporter...
Jul 08 21:31:11 vmi1561561.contaboserver.net systemd[1]: node_exporter.service: Deactivated successfully.
Jul 08 21:31:11 vmi1561561.contaboserver.net systemd[1]: Stopped Node Exporter.
```
