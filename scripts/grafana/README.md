[Back to Main README](../../README.md)

Grafana is used to create and customize dashboards for visualizing the metrics collected by Prometheus, providing an intuitive and powerful interface for monitoring your system performance.

<br />

---

- [Installation](#installation)
- [Uninstallation](#uninstallation)
- [Dashboard](#dashboard)

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

# Dashboard

To install a the dashboard, create a data source

1. Create a data source by going to `Open Menu > Data sources`
2. Click on `Add new data source`
3. Select `prometheus` type
4. Input `http://localhost:9090` for the prometheus server URL
5. Click on `Save & test`
6. Copy the data source uid from the url `http://x.x.x.x:3000/connections/datasources/edit/ddthq15b4mqkgc` (here the data source uid is ddthq15b4mqkgc)

Then, create the dasboard

1. Create a dashboard by going to `Open Menu > Dashboards`
2. Click on `Create dashboard`
3. Click on `Import a dashboard`
4. Copy the content of `scripts/grafana/grafana_dashboard.json` and past it in a editor
5. Replace `edr8vrdeu1mv4f` by your data source uid
6. Copy the updated grafana dashboard json
7. Past it in the section `Import via dasbboard JSON model`
8. Click on `Load`

You will be redirected to the dasboard whtn you can see the different KPIs. You have to wait some time to have data that can be useful.
