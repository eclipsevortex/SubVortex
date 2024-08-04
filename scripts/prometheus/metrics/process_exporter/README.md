[Back to Prometheus](../../README.md)

Process exporter is a tool that monitors specific system processes and provides detailed metrics about their performance and state, allowing for comprehensive process-level monitoring and alerting.

<br />

---

- [Installation](#installation)
- [Uninstallation](#uninstallation)

<br />

# Installation

To install Node Exporter, run:

```bash
./scripts/prometheus/metrics/process_exporter/process_exporter_setup.sh
```

Next, start it with:

```bash
./scripts/prometheus/metrics/process_exporter/process_exporter_start.sh
```

To check the service is up and running

```bash
sudo systemctl status process_exporter
```

You should see something like

```bash
● process_exporter.service - Process Exporter
     Loaded: loaded (/etc/systemd/system/process_exporter.service; enabled; vendor preset: enabled)
     Active: active (running) since Tue 2024-07-09 10:25:25 CEST; 1min 31s ago
   Main PID: 366355 (process-exporte)
      Tasks: 9 (limit: 19117)
     Memory: 12.3M
        CPU: 618ms
     CGroup: /system.slice/process_exporter.service
             └─366355 /usr/local/bin/process-exporter

Jul 09 10:25:25 vmi1561561.contaboserver.net systemd[1]: Started Process Exporter.
Jul 09 10:25:25 vmi1561561.contaboserver.net process-exporter[366355]: 2024/07/09 10:25:25 Reading metrics from /proc for procnames: []
```

<br />

# Uninstallation

To uninstall Node Exporter, first stop the service:

```bash
./scripts/prometheus/metrics/process_exporter/process_exporter_stop.sh
```

Then, you can uninstall it by running:

```bash
./scripts/prometheus/metrics/process_exporter/process_exporter_teardown.sh
```

To check the service is down

```bash
sudo systemctl status process_exporter
```

You should see something like

```bash
○ process_exporter.service - Process Exporter
     Loaded: loaded (/etc/systemd/system/process_exporter.service; enabled; vendor preset: enabled)
     Active: inactive (dead) since Tue 2024-07-09 10:48:26 CEST; 1s ago
    Process: 367030 ExecStart=/usr/local/bin/process-exporter --config.path /etc/process-exporter/config.yml (code=killed, signal=TERM)
   Main PID: 367030 (code=killed, signal=TERM)
        CPU: 17.573s

Jul 09 10:32:48 vmi1561561.contaboserver.net systemd[1]: Started Process Exporter.
Jul 09 10:32:48 vmi1561561.contaboserver.net process-exporter[367030]: 2024/07/09 10:32:48 Reading metrics from /proc based on "/etc/process-exporter/config.>
Jul 09 10:48:26 vmi1561561.contaboserver.net systemd[1]: Stopping Process Exporter...
Jul 09 10:48:26 vmi1561561.contaboserver.net systemd[1]: process_exporter.service: Deactivated successfully.
Jul 09 10:48:26 vmi1561561.contaboserver.net systemd[1]: Stopped Process Exporter.
Jul 09 10:48:26 vmi1561561.contaboserver.net systemd[1]: process_exporter.service: Consumed 17.573s CPU time.
```
